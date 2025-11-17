"""
Compliance Comparator

Core comparison logic for comparing policies against regulations.
"""

from typing import Dict, Any, List, Tuple, Optional
from enum import Enum


class ComplianceStatus(Enum):
    """Compliance status levels."""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNCLEAR = "unclear"


class ComplianceComparator:
    """
    Core comparator for policy-regulation comparison.
    
    Provides methods for semantic comparison and compliance assessment.
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize the compliance comparator.
        
        Args:
            similarity_threshold: Minimum similarity score for compliance (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def compare(
        self,
        policy_text: str,
        regulation_text: str,
        regulation_article: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare policy text against regulation text.
        
        Args:
            policy_text: Policy document content
            regulation_text: Regulation content to compare against
            regulation_article: Optional article number for citation
        
        Returns:
            Comparison result dictionary
        """
        # Basic text-based comparison
        similarity = self._calculate_text_similarity(policy_text, regulation_text)
        
        # Check for key requirements
        requirements_check = self._check_requirements(policy_text, regulation_text)
        
        # Determine compliance status
        status = self._determine_status(similarity, requirements_check)
        
        return {
            "similarity_score": similarity,
            "compliance_status": status.value,
            "requirements_met": requirements_check["met"],
            "requirements_missing": requirements_check["missing"],
            "regulation_article": regulation_article,
            "has_discrepancy": status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT]
        }
    
    def _calculate_text_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Uses simple word overlap as baseline.
        Can be enhanced with embeddings/semantic similarity models.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score (0-1)
        """
        # Simple word-based similarity (Jaccard)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _check_requirements(
        self,
        policy_text: str,
        regulation_text: str
    ) -> Dict[str, Any]:
        """
        Check if policy addresses requirements mentioned in regulation.
        
        Args:
            policy_text: Policy content
            regulation_text: Regulation content
        
        Returns:
            Dictionary with requirements check results
        """
        policy_lower = policy_text.lower()
        regulation_lower = regulation_text.lower()
        
        # Extract requirement keywords from regulation
        requirement_keywords = self._extract_requirement_keywords(regulation_lower)
        
        met = []
        missing = []
        
        for keyword, context in requirement_keywords:
            if keyword in policy_lower:
                met.append(f"{keyword} (found in policy)")
            else:
                missing.append(f"{keyword} (not found in policy)")
        
        return {
            "met": met,
            "missing": missing,
            "total_requirements": len(requirement_keywords)
        }
    
    def _extract_requirement_keywords(
        self,
        regulation_text: str
    ) -> List[Tuple[str, str]]:
        """
        Extract requirement keywords from regulation text.
        
        Args:
            regulation_text: Regulation content
        
        Returns:
            List of (keyword, context) tuples
        """
        keywords = []
        
        # Look for requirement patterns
        import re
        
        # Patterns like "must", "shall", "required", "shall ensure"
        requirement_patterns = [
            r'(?:must|shall|required|shall ensure)\s+([^\.]+)',
            r'requires?\s+([^\.]+)',
            r'ensure\s+([^\.]+)',
        ]
        
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, regulation_text, re.IGNORECASE)
            for match in matches:
                requirement_text = match.group(1).strip()
                # Extract key words (nouns, verbs)
                key_words = requirement_text.split()[:5]  # First 5 words
                keyword = " ".join(key_words).lower()
                keywords.append((keyword, requirement_text))
        
        return keywords[:10]  # Limit to 10 requirements
    
    def _determine_status(
        self,
        similarity: float,
        requirements_check: Dict[str, Any]
    ) -> ComplianceStatus:
        """Determine compliance status based on similarity and requirements."""
        total_reqs = requirements_check["total_requirements"]
        met_reqs = len(requirements_check["met"])
        
        if total_reqs == 0:
            # No explicit requirements found, use similarity
            if similarity >= self.similarity_threshold:
                return ComplianceStatus.COMPLIANT
            elif similarity >= self.similarity_threshold * 0.7:
                return ComplianceStatus.PARTIALLY_COMPLIANT
            else:
                return ComplianceStatus.NON_COMPLIANT
        
        # Use requirement coverage
        coverage = met_reqs / total_reqs if total_reqs > 0 else 0
        
        if coverage >= 0.8 and similarity >= self.similarity_threshold * 0.8:
            return ComplianceStatus.COMPLIANT
        elif coverage >= 0.5:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        elif coverage < 0.5 or similarity < self.similarity_threshold * 0.5:
            return ComplianceStatus.NON_COMPLIANT
        else:
            return ComplianceStatus.UNCLEAR
    
    def batch_compare(
        self,
        policy_chunks: List[str],
        regulation_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple policy chunks against regulations.
        
        Args:
            policy_chunks: List of policy text chunks
            regulation_chunks: List of regulation dictionaries with content
        
        Returns:
            List of comparison results
        """
        results = []
        
        for policy_chunk in policy_chunks:
            best_match = None
            best_score = 0.0
            
            # Find best matching regulation for this chunk
            for reg_chunk in regulation_chunks:
                reg_content = reg_chunk.get("content", "")
                reg_article = reg_chunk.get("regulation_type", "Unknown")
                
                comparison = self.compare(
                    policy_chunk,
                    reg_content,
                    reg_article
                )
                
                if comparison["similarity_score"] > best_score:
                    best_score = comparison["similarity_score"]
                    best_match = comparison
            
            if best_match:
                results.append(best_match)
        
        return results
