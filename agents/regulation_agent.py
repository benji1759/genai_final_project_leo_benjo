"""
Regulation Agent

Responsible for retrieving relevant EU regulations via RAG
based on policy document content.
"""

from typing import Dict, Any, List
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from agents.base import BaseAgent


class RegulationAgent(BaseAgent):
    """
    Agent specialized in retrieving relevant EU regulations.
    
    This agent uses RAG to find and retrieve relevant regulation sections
    based on policy document content or specific queries.
    """
    
    def __init__(
        self,
        chroma_dir: str = "chroma_eu_laws",
        embed_model: str = "text-embedding-3-small",
        retrieval_k: int = 5,
        **kwargs
    ):
        """
        Initialize the regulation agent.
        
        Args:
            chroma_dir: Directory containing ChromaDB regulation database
            embed_model: Embedding model name
            retrieval_k: Number of regulation chunks to retrieve
            **kwargs: Additional arguments for BaseAgent
        """
        super().__init__(
            agent_id="regulation_agent",
            agent_name="Regulation Retrieval Agent",
            **kwargs
        )
        
        self.chroma_dir = chroma_dir
        self.embed_model = embed_model
        self.retrieval_k = retrieval_k
        
        # Initialize embeddings and vector store
        self.embedding = OpenAIEmbeddings(model=embed_model)
        self.vectorstore = Chroma(
            persist_directory=chroma_dir,
            embedding_function=self.embedding
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": retrieval_k}
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant regulations for a given query or document.
        
        Expected input_data:
            - query: Search query or document content
            - regulation_types: Optional list of regulation types to filter (e.g., ["GDPR", "AI Act"])
        
        Returns:
            Dictionary containing:
                - retrieved_regulations: List of retrieved regulation chunks
                - relevance_scores: Relevance information
                - regulation_types: Types of regulations found
        """
        # Validate input
        self.validate_input(input_data, ["query"])
        
        query = input_data["query"]
        regulation_types = input_data.get("regulation_types", None)
        
        self.log(f"Retrieving regulations for query: {query[:100]}...")
        
        try:
            # Retrieve relevant documents
            docs = self.retriever.invoke(query)
            
            # Process retrieved documents
            retrieved_regulations = []
            regulation_types_found = set()
            
            for doc in docs:
                # Extract metadata if available
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                # Try to identify regulation type from metadata or content
                reg_type = self._identify_regulation_type(doc.page_content, metadata)
                if reg_type:
                    regulation_types_found.add(reg_type)
                
                retrieved_regulations.append({
                    "content": doc.page_content,
                    "metadata": metadata,
                    "regulation_type": reg_type,
                    "source": metadata.get("source", "Unknown")
                })
            
            # Filter by regulation types if specified
            if regulation_types:
                retrieved_regulations = [
                    reg for reg in retrieved_regulations
                    if reg["regulation_type"] in regulation_types or reg["regulation_type"] is None
                ]
            
            # Store results in state
            if self.state:
                self.store_result("retrieved_regulations", retrieved_regulations)
                self.update_state_context("regulation_types", list(regulation_types_found))
            
            output = {
                "retrieved_regulations": retrieved_regulations,
                "num_retrieved": len(retrieved_regulations),
                "regulation_types": list(regulation_types_found),
                "query": query
            }
            
            self.log(f"Retrieved {len(retrieved_regulations)} regulation chunks")
            
            return output
        
        except Exception as e:
            error_msg = f"Error retrieving regulations: {str(e)}"
            self.log(error_msg, level="ERROR")
            raise RuntimeError(error_msg) from e
    
    def _identify_regulation_type(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Identify the type of regulation from content or metadata.
        
        Args:
            content: Regulation text content
            metadata: Document metadata
        
        Returns:
            Regulation type name (e.g., "GDPR", "AI Act", "NIS2") or None
        """
        # Check metadata first
        source = metadata.get("source", "").lower()
        
        regulation_keywords = {
            "GDPR": ["gdpr", "general data protection", "regulation 2016/679"],
            "AI Act": ["ai act", "artificial intelligence act", "regulation 2024/..."],
            "NIS2": ["nis2", "network and information systems", "directive 2022/2555"],
            "DSA": ["digital services act", "dsa", "regulation 2022/2065"],
            "DMA": ["digital markets act", "dma", "regulation 2022/1925"]
        }
        
        # Check source filename
        for reg_type, keywords in regulation_keywords.items():
            if any(keyword in source for keyword in keywords):
                return reg_type
        
        # Check content for regulation mentions
        content_lower = content.lower()
        for reg_type, keywords in regulation_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return reg_type
        
        return None
    
    def retrieve_for_document_chunks(
        self,
        document_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve regulations for multiple document chunks.
        
        Args:
            document_chunks: List of document chunk dictionaries
        
        Returns:
            Dictionary mapping chunk IDs to retrieved regulations
        """
        chunk_regulations = {}
        
        for chunk in document_chunks:
            chunk_id = chunk.get("chunk_id", 0)
            content = chunk.get("content", "")
            
            # Retrieve regulations for this chunk
            query_result = self.execute({"query": content})
            chunk_regulations[chunk_id] = query_result["retrieved_regulations"]
        
        return {
            "chunk_regulations": chunk_regulations,
            "total_chunks_processed": len(document_chunks)
        }
