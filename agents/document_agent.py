"""
Document Agent

Responsible for parsing and structuring uploaded policy documents.
"""

from typing import Dict, Any, List
from pathlib import Path

from agents.base import BaseAgent
from document_parser import DocumentParser, ParsedDocument


class DocumentAgent(BaseAgent):
    """
    Agent specialized in parsing and structuring policy documents.
    
    This agent handles document upload, parsing, and initial structuring
    for further analysis by other agents.
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ):
        """
        Initialize the document agent.
        
        Args:
            llm_model: LLM model to use
            chunk_size: Target chunk size for document parsing
            chunk_overlap: Overlap between chunks
            **kwargs: Additional arguments for BaseAgent
        """
        super().__init__(
            agent_id="document_agent",
            agent_name="Document Parser Agent",
            llm_model=llm_model,
            **kwargs
        )
        
        self.parser = DocumentParser(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            semantic_chunking=True
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and structure a document.
        
        Expected input_data:
            - file_path: Path to the document file
            - document_id: Optional unique identifier for the document
        
        Returns:
            Dictionary containing:
                - document_id: Unique identifier
                - parsed_document: ParsedDocument object
                - chunks: List of document chunks
                - metadata: Document metadata
        """
        # Validate input
        self.validate_input(input_data, ["file_path"])
        
        file_path = input_data["file_path"]
        document_id = input_data.get("document_id", Path(file_path).stem)
        
        self.log(f"Parsing document: {file_path}")
        
        try:
            # Parse the document
            parsed_doc = self.parser.parse_file(file_path)
            
            # Store document information in state
            if self.state:
                self.update_state_context("document_id", document_id)
                self.update_state_context("document_title", parsed_doc.title)
                self.update_state_context("document_type", parsed_doc.file_type)
                self.store_result("parsed_document", parsed_doc)
            
            # Prepare output
            output = {
                "document_id": document_id,
                "parsed_document": parsed_doc,
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "section": chunk.section,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char
                    }
                    for chunk in parsed_doc.chunks
                ],
                "metadata": {
                    "filename": parsed_doc.filename,
                    "file_type": parsed_doc.file_type,
                    "title": parsed_doc.title,
                    "author": parsed_doc.author,
                    "date": parsed_doc.date.isoformat() if parsed_doc.date else None,
                    "num_chunks": len(parsed_doc.chunks),
                    "total_length": len(parsed_doc.full_text),
                    **parsed_doc.metadata
                }
            }
            
            self.log(f"Document parsed successfully: {len(parsed_doc.chunks)} chunks created")
            
            return output
        
        except Exception as e:
            error_msg = f"Error parsing document: {str(e)}"
            self.log(error_msg, level="ERROR")
            raise RuntimeError(error_msg) from e
    
    def extract_sections(self, parsed_document: ParsedDocument) -> Dict[str, List[str]]:
        """
        Extract document sections for structured analysis.
        
        Args:
            parsed_document: Parsed document object
        
        Returns:
            Dictionary mapping section names to their content chunks
        """
        sections = {}
        
        for chunk in parsed_document.chunks:
            section_name = chunk.section or "Introduction"
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(chunk.content)
        
        return sections
    
    def get_document_summary(self, parsed_document: ParsedDocument) -> str:
        """
        Generate a brief summary of the document using LLM.
        
        Args:
            parsed_document: Parsed document object
        
        Returns:
            Document summary string
        """
        # Use first few chunks for summary
        summary_chunks = parsed_document.chunks[:3]
        content_preview = "\n\n".join([chunk.content for chunk in summary_chunks])
        
        prompt = f"""
You are a document analyst. Provide a concise summary (2-3 sentences) of the following policy document.

Document Title: {parsed_document.title or "Unknown"}
Document Preview:
{content_preview[:1000]}

Summary:
"""
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
