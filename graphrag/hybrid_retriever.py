"""
Hybrid Retriever

Combines vector similarity search with graph traversal for enhanced retrieval.
"""

from typing import Dict, Any, List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from graphrag.graph_store import GraphStore
from graphrag.entity_extractor import RegulationEntity


class HybridRetriever:
    """
    Hybrid retriever combining vector search with knowledge graph traversal.
    
    Uses vector similarity for initial retrieval, then enhances with
    graph-based relationships for better context.
    """
    
    def __init__(
        self,
        vectorstore: Chroma,
        graph_store: GraphStore,
        embed_model: str = "text-embedding-3-small",
        vector_k: int = 5,
        graph_depth: int = 2
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            vectorstore: ChromaDB vector store for regulations
            graph_store: Knowledge graph store
            embed_model: Embedding model name
            vector_k: Number of documents to retrieve from vector store
            graph_depth: Maximum depth for graph traversal
        """
        self.vectorstore = vectorstore
        self.graph_store = graph_store
        self.embed_model = embed_model
        self.vector_k = vector_k
        self.graph_depth = graph_depth
        
        # Initialize retriever
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": vector_k})
        self.embedding = OpenAIEmbeddings(model=embed_model)
    
    def retrieve(
        self,
        query: str,
        regulation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant regulations using hybrid approach.
        
        Args:
            query: Search query
            regulation_types: Optional filter by regulation types
        
        Returns:
            Dictionary containing retrieved documents and graph-enhanced context
        """
        # Step 1: Vector similarity search
        vector_results = self._vector_search(query)
        
        # Step 2: Extract entities from query and retrieved docs
        query_entities = self._extract_query_entities(query)
        
        # Step 3: Enhance with graph relationships
        enhanced_results = self._enhance_with_graph(
            vector_results,
            query_entities,
            regulation_types
        )
        
        return {
            "vector_results": vector_results,
            "query_entities": query_entities,
            "enhanced_results": enhanced_results,
            "retrieved_documents": enhanced_results["documents"]
        }
    
    def _vector_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        docs = self.retriever.invoke(query)
        
        results = []
        for doc in docs:
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            results.append({
                "content": doc.page_content,
                "metadata": metadata,
                "source": metadata.get("source", "Unknown")
            })
        
        return results
    
    def _extract_query_entities(self, query: str) -> List[str]:
        """Extract potential entity references from query."""
        import re
        
        entities = []
        
        # Look for article references
        article_pattern = r'(?i)article\s+(\d+)'
        article_matches = re.finditer(article_pattern, query)
        
        for match in article_matches:
            article_num = match.group(1)
            entities.append(article_num)
        
        # Look for regulation types
        regulation_keywords = {
            "GDPR": ["gdpr", "general data protection"],
            "AI Act": ["ai act", "artificial intelligence act"],
            "NIS2": ["nis2", "network and information systems"]
        }
        
        query_lower = query.lower()
        for reg_type, keywords in regulation_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                entities.append(reg_type)
        
        return entities
    
    def _enhance_with_graph(
        self,
        vector_results: List[Dict[str, Any]],
        query_entities: List[str],
        regulation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Enhance retrieval results with graph relationships."""
        enhanced_docs = []
        related_entities = []
        
        # For each retrieved document, find related entities in graph
        for doc in vector_results:
            # Try to identify entities in document
            doc_content = doc["content"]
            doc_metadata = doc.get("metadata", {})
            reg_type = doc_metadata.get("regulation_type", None)
            
            # Find entities matching document content
            doc_entities = self._find_entities_for_document(
                doc_content,
                reg_type
            )
            
            # Get related entities from graph
            for entity_id in doc_entities:
                related = self.graph_store.get_related_entities(
                    entity_id,
                    relationship_type=None
                )
                
                # Filter by regulation type if specified
                if regulation_types:
                    related = [
                        rel for rel in related
                        if rel.get("regulation_type") in regulation_types
                    ]
                
                related_entities.extend(related)
            
            enhanced_docs.append({
                **doc,
                "entities": doc_entities,
                "related_count": len(doc_entities)
            })
        
        # Remove duplicate entities
        unique_related = self._deduplicate_entities(related_entities)
        
        # Re-rank documents based on graph relationships
        enhanced_docs = self._rerank_with_graph(
            enhanced_docs,
            query_entities
        )
        
        return {
            "documents": enhanced_docs,
            "related_entities": unique_related,
            "num_related_entities": len(unique_related)
        }
    
    def _find_entities_for_document(
        self,
        content: str,
        regulation_type: Optional[str] = None
    ) -> List[str]:
        """Find entity IDs that match document content."""
        import re
        
        entity_ids = []
        
        # Extract article numbers
        article_pattern = r'(?i)article\s+(\d+(?:-\d+)?)'
        article_matches = re.finditer(article_pattern, content)
        
        for match in article_matches:
            article_num = match.group(1)
            entity_id = f"{regulation_type}_article_{article_num}" if regulation_type else f"article_{article_num}"
            entity_ids.append(entity_id)
        
        return entity_ids
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities."""
        seen_ids = set()
        unique = []
        
        for entity in entities:
            entity_id = entity.get("id", "")
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                unique.append(entity)
        
        return unique
    
    def _rerank_with_graph(
        self,
        documents: List[Dict[str, Any]],
        query_entities: List[str]
    ) -> List[Dict[str, Any]]:
        """Re-rank documents based on graph relationships to query entities."""
        scored_docs = []
        
        for doc in documents:
            score = doc.get("score", 1.0)  # Base score from vector search
            
            # Boost score if document entities relate to query entities
            doc_entities = doc.get("entities", [])
            
            for query_entity in query_entities:
                # Check if query entity matches any document entity
                for doc_entity_id in doc_entities:
                    # Simple check: entity ID contains query entity
                    if query_entity in doc_entity_id or query_entity.lower() in doc_entity_id.lower():
                        score += 0.2  # Boost for entity match
                        
                        # Check graph path
                        path = self.graph_store.find_path(
                            query_entity,
                            doc_entity_id,
                            max_length=self.graph_depth
                        )
                        
                        if path:
                            # Boost based on path length (closer = better)
                            path_boost = 0.3 / len(path)
                            score += path_boost
            
            scored_docs.append({
                **doc,
                "score": score
            })
        
        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return scored_docs
    
    def get_article_context(
        self,
        article_ref: str,
        regulation_type: str
    ) -> Dict[str, Any]:
        """
        Get enhanced context for a specific article using graph.
        
        Args:
            article_ref: Article reference (e.g., "25")
            regulation_type: Regulation type (e.g., "GDPR")
        
        Returns:
            Dictionary with article content and related information
        """
        entity_id = f"{regulation_type}_article_{article_ref}"
        
        # Get entity
        entity = self.graph_store.get_entity(entity_id)
        
        if not entity:
            return {"found": False}
        
        # Get related entities
        related = self.graph_store.get_related_entities(entity_id)
        
        # Find in vector store for full content
        query = f"Article {article_ref} {regulation_type}"
        vector_results = self._vector_search(query)
        
        return {
            "found": True,
            "entity": entity,
            "related_entities": related,
            "full_content": vector_results[0]["content"] if vector_results else None
        }
