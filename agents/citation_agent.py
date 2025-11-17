"""
Citation Agent

Responsible for extracting and validating article citations
from regulations and comparison results.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from agents.base import BaseAgent


class CitationAgent(BaseAgent):
    """
    Agent specialized in extracting and validating regulation citations.
    
    This agent identifies article numbers, clause references, and validates
    their correctness against regulation texts.
    """
    
    def __init__(self, **kwargs):
        """Initialize the citation agent."""
        super().__init__(
            agent_id="citation_agent",
            agent_name="Citation Extraction Agent",
            temperature=0.0,  # Zero temperature for consistent extraction
            **kwargs
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate citations from text.
        
        Expected input_data:
            - text: Text content to extract citations from
            - regulation_type: Optional regulation type (GDPR, AI Act, etc.)
            - context: Optional regulation context for validation
        
        Returns:
            Dictionary containing:
                - citations: List of extracted citations
                - validated_citations: List of validated citations with context
        """
        # Validate input
        self.validate_input(input_data, ["text"])
        
        text = input_data["text"]
        regulation_type = input_data.get("regulation_type", None)
        context = input_data.get("context", None)
        
        self.log(f"Extracting citations from text (regulation: {regulation_type})")
        
        try:
            # Extract citations using patterns
            citations = self._extract_citations(text, regulation_type)
            
            # Validate citations if context is provided
            validated_citations = []
            if context:
                validated_citations = self._validate_citations(
                    citations,
                    context,
                    regulation_type
                )
            else:
                # Use LLM to extract context for citations
                validated_citations = self._extract_citation_context(
                    citations,
                    text,
                    regulation_type
                )
            
            output = {
                "citations": citations,
                "validated_citations": validated_citations,
                "num_citations": len(citations),
                "regulation_type": regulation_type
            }
            
            # Store results in state
            if self.state:
                self.store_result("citations", output)
            
            self.log(f"Extracted {len(citations)} citations")
            
            return output
        
        except Exception as e:
            error_msg = f"Error extracting citations: {str(e)}"
            self.log(error_msg, level="ERROR")
            raise RuntimeError(error_msg) from e
    
    def _extract_citations(
        self,
        text: str,
        regulation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract citation patterns from text.
        
        Citation patterns:
        - Article X
        - Art. X
        - Article X, paragraph Y
        - Article X(Y)
        - Article X-Y
        - GDPR Article X
        - Regulation X/YYYY
        """
        citations = []
        
        # Common citation patterns
        patterns = [
            # Article X
            r'(?i)(?:article|art\.?)\s+(\d+(?:-\d+)?(?:\([a-z0-9]+\))?)',
            # GDPR Article X
            r'(?i)gdpr\s+(?:article|art\.?)\s+(\d+(?:-\d+)?)',
            # AI Act Article X
            r'(?i)ai\s+act\s+(?:article|art\.?)\s+(\d+(?:-\d+)?)',
            # Regulation X/YYYY
            r'(?i)regulation\s+(\d+/\d{4})',
            # Directive X/YYYY
            r'(?i)directive\s+(\d+/\d{4})',
            # Paragraph/Clause references
            r'(?i)paragraph\s+(\d+[a-z]?)',
            r'(?i)clause\s+(\d+[a-z]?)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                article_ref = match.group(1)
                
                # Extract surrounding context (50 chars before/after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                citations.append({
                    "reference": article_ref,
                    "full_match": match.group(0),
                    "context": context,
                    "position": match.start(),
                    "regulation_type": regulation_type or self._infer_regulation_type(article_ref, context)
                })
        
        # Remove duplicates based on reference and position proximity
        unique_citations = self._deduplicate_citations(citations)
        
        return unique_citations
    
    def _infer_regulation_type(
        self,
        reference: str,
        context: str
    ) -> Optional[str]:
        """Infer regulation type from reference and context."""
        context_lower = context.lower()
        
        regulation_keywords = {
            "GDPR": ["gdpr", "data protection", "regulation 2016/679"],
            "AI Act": ["ai act", "artificial intelligence", "regulation 2024"],
            "NIS2": ["nis2", "network and information systems", "directive 2022/2555"],
            "DSA": ["digital services act", "dsa", "regulation 2022/2065"],
            "DMA": ["digital markets act", "dma", "regulation 2022/1925"]
        }
        
        for reg_type, keywords in regulation_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                return reg_type
        
        return None
    
    def _deduplicate_citations(
        self,
        citations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate citations that are close together."""
        if not citations:
            return []
        
        # Sort by position
        sorted_citations = sorted(citations, key=lambda x: x["position"])
        unique = [sorted_citations[0]]
        
        for citation in sorted_citations[1:]:
            last_citation = unique[-1]
            
            # Consider duplicate if same reference and within 100 chars
            is_duplicate = (
                citation["reference"] == last_citation["reference"] and
                citation["position"] - last_citation["position"] < 100
            )
            
            if not is_duplicate:
                unique.append(citation)
        
        return unique
    
    def _validate_citations(
        self,
        citations: List[Dict[str, Any]],
        regulation_context: str,
        regulation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Validate citations against regulation context."""
        validated = []
        
        for citation in citations:
            ref = citation["reference"]
            
            # Search for the article in context
            is_valid = self._check_article_exists(ref, regulation_context)
            
            validated.append({
                **citation,
                "validated": is_valid,
                "validation_source": "context_check"
            })
        
        return validated
    
    def _check_article_exists(
        self,
        article_ref: str,
        context: str
    ) -> bool:
        """Check if article reference exists in context."""
        # Normalize article reference
        article_num = re.search(r'\d+', article_ref)
        if not article_num:
            return False
        
        article_num = article_num.group(0)
        
        # Look for article in context (case-insensitive)
        patterns = [
            rf'(?i)article\s+{article_num}\b',
            rf'(?i)art\.?\s+{article_num}\b',
        ]
        
        for pattern in patterns:
            if re.search(pattern, context):
                return True
        
        return False
    
    def _extract_citation_context(
        self,
        citations: List[Dict[str, Any]],
        source_text: str,
        regulation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Use LLM to extract context for citations."""
        validated = []
        
        for citation in citations:
            ref = citation["reference"]
            context = citation["context"]
            
            # Build prompt to extract citation meaning
            prompt = f"""
Extract the meaning and relevance of the following regulation citation.

Citation: {ref}
Context: {context}
Regulation Type: {regulation_type or "Unknown"}

Provide:
1. The article number or clause
2. What this citation refers to
3. The relevance in the context

Format:
Article: [number]
Meaning: [brief description]
Relevance: [how it's relevant in context]
"""
            
            response = self.llm.invoke(prompt)
            citation_meaning = response.content.strip()
            
            validated.append({
                **citation,
                "validated": True,
                "validation_source": "llm_extraction",
                "citation_meaning": citation_meaning
            })
        
        return validated
    
    def extract_citations_from_comparison(
        self,
        comparison_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract citations from comparison results.
        
        Args:
            comparison_results: Results from comparison agent
        
        Returns:
            Dictionary with citations organized by type
        """
        all_text = comparison_results.get("raw_analysis", "")
        
        # Extract citations
        citations_result = self.execute({
            "text": all_text,
            "regulation_type": None
        })
        
        # Organize citations by regulation type
        citations_by_type = {}
        for citation in citations_result["citations"]:
            reg_type = citation.get("regulation_type", "Unknown")
            if reg_type not in citations_by_type:
                citations_by_type[reg_type] = []
            citations_by_type[reg_type].append(citation)
        
        return {
            "all_citations": citations_result["citations"],
            "citations_by_regulation": citations_by_type,
            "num_citations": len(citations_result["citations"])
        }
