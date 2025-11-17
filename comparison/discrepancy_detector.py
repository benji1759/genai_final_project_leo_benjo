"""
Discrepancy Detector

Identifies and flags discrepancies between policies and regulations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class DiscrepancyType(Enum):
    """Types of discrepancies."""
    MISSING_REQUIREMENT = "missing_requirement"
    CONFLICT = "conflict"
    INCOMPLETE = "incomplete"
    UNCLEAR = "unclear"


@dataclass
class Discrepancy:
    """Represents a compliance discrepancy."""
    type: DiscrepancyType
    description: str
    policy_text: Optional[str] = None
    regulation_article: Optional[str] = None
    severity: str = "medium"
    position: Optional[int] = None


class DiscrepancyDetector:
    """
    Detects discrepancies between policies and regulations.
    
    Identifies missing requirements, conflicts, and incomplete implementations.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the discrepancy detector.
        
        Args:
            strict_mode: If True, flag even minor discrepancies
        """
        self.strict_mode = strict_mode
    
    def detect_discrepancies(
        self,
        comparison_results: Dict[str, Any],
        policy_text: str,
        regulation_texts: List[Dict[str, Any]]
    ) -> List[Discrepancy]:
        """
        Detect discrepancies from comparison results.
        
        Args:
            comparison_results: Results from compliance comparison
            policy_text: Policy document content
            regulation_texts: List of regulation chunks
        
        Returns:
            List of Discrepancy objects
        """
        discrepancies = []
        
        # Check compliance status
        status = comparison_results.get("compliance_status", "")
        
        if status in ["non_compliant", "partially_compliant"]:
            # Extract specific discrepancies
            discrepancies.extend(
                self._extract_status_discrepancies(
                    comparison_results,
                    policy_text,
                    regulation_texts
                )
            )
        
        # Check missing requirements
        missing_reqs = comparison_results.get("requirements_missing", [])
        for missing in missing_reqs:
            discrepancies.append(
                Discrepancy(
                    type=DiscrepancyType.MISSING_REQUIREMENT,
                    description=missing,
                    severity="high"
                )
            )
        
        # Check for conflicts
        conflicts = self._detect_conflicts(policy_text, regulation_texts)
        discrepancies.extend(conflicts)
        
        # Check for incomplete implementations
        incomplete = self._detect_incomplete(policy_text, regulation_texts)
        discrepancies.extend(incomplete)
        
        return discrepancies
    
    def _extract_status_discrepancies(
        self,
        comparison_results: Dict[str, Any],
        policy_text: str,
        regulation_texts: List[Dict[str, Any]]
    ) -> List[Discrepancy]:
        """Extract discrepancies from non-compliant status."""
        discrepancies = []
        
        similarity = comparison_results.get("similarity_score", 0)
        
        if similarity < 0.5:
            discrepancies.append(
                Discrepancy(
                    type=DiscrepancyType.CONFLICT,
                    description=f"Low similarity score ({similarity:.2f}) indicates potential conflict with regulations",
                    severity="high"
                )
            )
        
        return discrepancies
    
    def _detect_conflicts(
        self,
        policy_text: str,
        regulation_texts: List[Dict[str, Any]]
    ) -> List[Discrepancy]:
        """Detect direct conflicts between policy and regulations."""
        conflicts = []
        
        policy_lower = policy_text.lower()
        
        # Look for conflicting language patterns
        conflict_indicators = [
            ("prohibited", "allows"),
            ("required", "does not require"),
            ("must", "may not"),
        ]
        
        for reg_chunk in regulation_texts:
            reg_content = reg_chunk.get("content", "").lower()
            reg_article = reg_chunk.get("regulation_type", "Unknown")
            
            for prohibited, allowed in conflict_indicators:
                if prohibited in reg_content and allowed in policy_lower:
                    conflicts.append(
                        Discrepancy(
                            type=DiscrepancyType.CONFLICT,
                            description=f"Policy allows '{allowed}' but regulation '{reg_article}' requires '{prohibited}'",
                            regulation_article=reg_article,
                            severity="critical"
                        )
                    )
        
        return conflicts
    
    def _detect_incomplete(
        self,
        policy_text: str,
        regulation_texts: List[Dict[str, Any]]
    ) -> List[Discrepancy]:
        """Detect incomplete implementations of requirements."""
        incomplete = []
        
        policy_lower = policy_text.lower()
        
        # Look for requirement patterns that might be incomplete
        requirement_verbs = ["must", "shall", "required", "ensure"]
        
        for reg_chunk in regulation_texts:
            reg_content = reg_chunk.get("content", "")
            reg_article = reg_chunk.get("regulation_type", "Unknown")
            
            # Check if regulation mentions multiple requirements
            sentences = reg_content.split('.')
            requirements_mentioned = []
            
            for sentence in sentences:
                if any(verb in sentence.lower() for verb in requirement_verbs):
                    # Extract the requirement
                    requirement_text = sentence.strip()
                    if requirement_text:
                        requirements_mentioned.append(requirement_text)
            
            # Check if policy addresses all mentioned requirements
            for req in requirements_mentioned:
                # Simple check: see if key words from requirement are in policy
                req_words = set(req.lower().split()[:5])  # First 5 words
                policy_words = set(policy_lower.split())
                
                overlap = len(req_words.intersection(policy_words))
                
                if overlap < len(req_words) * 0.3:  # Less than 30% overlap
                    incomplete.append(
                        Discrepancy(
                            type=DiscrepancyType.INCOMPLETE,
                            description=f"Requirement from '{reg_article}' may not be fully addressed: {req[:100]}",
                            regulation_article=reg_article,
                            severity="medium"
                        )
                    )
        
        return incomplete
    
    def flag_discrepancies(
        self,
        discrepancies: List[Discrepancy],
        min_severity: str = "low"
    ) -> List[Discrepancy]:
        """
        Filter discrepancies by minimum severity.
        
        Args:
            discrepancies: List of discrepancies
            min_severity: Minimum severity level ("low", "medium", "high", "critical")
        
        Returns:
            Filtered list of discrepancies
        """
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_levels.get(min_severity, 0)
        
        return [
            disc for disc in discrepancies
            if severity_levels.get(disc.severity, 0) >= min_level
        ]
