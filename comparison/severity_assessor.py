"""
Severity Assessor

Classifies discrepancies by severity level (critical, major, minor).
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from comparison.discrepancy_detector import Discrepancy, DiscrepancyType
from langchain_openai import ChatOpenAI


class SeverityLevel(Enum):
    """Severity levels for discrepancies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SeverityAssessor:
    """
    Assesses and classifies discrepancy severity.
    
    Uses rule-based and LLM-based approaches to determine
    the severity of compliance issues.
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", use_llm: bool = True):
        """
        Initialize the severity assessor.
        
        Args:
            llm_model: LLM model for severity assessment
            use_llm: Whether to use LLM for assessment (otherwise rule-based)
        """
        self.use_llm = use_llm
        if use_llm:
            self.llm = ChatOpenAI(model=llm_model, temperature=0)
    
    def assess_severity(
        self,
        discrepancy: Discrepancy,
        regulation_context: Optional[str] = None
    ) -> Discrepancy:
        """
        Assess severity of a discrepancy.
        
        Args:
            discrepancy: Discrepancy object to assess
            regulation_context: Optional regulation context for assessment
        
        Returns:
            Discrepancy object with updated severity
        """
        if self.use_llm and regulation_context:
            severity = self._llm_assess_severity(discrepancy, regulation_context)
        else:
            severity = self._rule_based_assess_severity(discrepancy)
        
        discrepancy.severity = severity.value
        return discrepancy
    
    def assess_batch(
        self,
        discrepancies: List[Discrepancy],
        regulation_contexts: Optional[Dict[str, str]] = None
    ) -> List[Discrepancy]:
        """
        Assess severity for multiple discrepancies.
        
        Args:
            discrepancies: List of discrepancies
            regulation_contexts: Optional dictionary mapping article to context
        
        Returns:
            List of discrepancies with assessed severity
        """
        assessed = []
        
        for disc in discrepancies:
            context = None
            if regulation_contexts and disc.regulation_article:
                context = regulation_contexts.get(disc.regulation_article)
            
            assessed.append(self.assess_severity(disc, context))
        
        return assessed
    
    def _rule_based_assess_severity(self, discrepancy: Discrepancy) -> SeverityLevel:
        """Rule-based severity assessment."""
        # Critical: Conflicts, missing legal obligations
        if discrepancy.type == DiscrepancyType.CONFLICT:
            return SeverityLevel.CRITICAL
        
        # High: Missing requirements, incomplete critical elements
        if discrepancy.type == DiscrepancyType.MISSING_REQUIREMENT:
            # Check if it's a legal obligation
            description_lower = discrepancy.description.lower()
            if any(keyword in description_lower for keyword in ["must", "shall", "required", "legal obligation"]):
                return SeverityLevel.HIGH
            return SeverityLevel.MEDIUM
        
        # Medium: Incomplete implementations
        if discrepancy.type == DiscrepancyType.INCOMPLETE:
            return SeverityLevel.MEDIUM
        
        # Low: Unclear elements
        if discrepancy.type == DiscrepancyType.UNCLEAR:
            return SeverityLevel.LOW
        
        # Default based on current severity
        severity_map = {
            "critical": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW
        }
        
        return severity_map.get(discrepancy.severity, SeverityLevel.MEDIUM)
    
    def _llm_assess_severity(
        self,
        discrepancy: Discrepancy,
        regulation_context: str
    ) -> SeverityLevel:
        """Use LLM to assess severity."""
        prompt = f"""
You are a compliance expert. Assess the severity of the following compliance discrepancy.

Discrepancy Type: {discrepancy.type.value}
Description: {discrepancy.description}
Regulation Article: {discrepancy.regulation_article or "Unknown"}

Regulation Context:
{regulation_context[:1000]}

Classify the severity as one of:
- critical: Legal violations, conflicts with mandatory requirements, potential penalties
- high: Missing mandatory requirements, incomplete critical implementations
- medium: Missing recommended practices, incomplete non-critical implementations
- low: Minor issues, unclear language, best practice improvements

Respond with ONLY one word: critical, high, medium, or low
"""
        
        try:
            response = self.llm.invoke(prompt)
            severity_str = response.content.strip().lower()
            
            severity_map = {
                "critical": SeverityLevel.CRITICAL,
                "high": SeverityLevel.HIGH,
                "medium": SeverityLevel.MEDIUM,
                "low": SeverityLevel.LOW
            }
            
            return severity_map.get(severity_str, SeverityLevel.MEDIUM)
        except Exception:
            # Fallback to rule-based
            return self._rule_based_assess_severity(discrepancy)
    
    def categorize_by_severity(
        self,
        discrepancies: List[Discrepancy]
    ) -> Dict[SeverityLevel, List[Discrepancy]]:
        """
        Categorize discrepancies by severity level.
        
        Args:
            discrepancies: List of discrepancies
        
        Returns:
            Dictionary mapping severity levels to discrepancy lists
        """
        categorized = {
            SeverityLevel.CRITICAL: [],
            SeverityLevel.HIGH: [],
            SeverityLevel.MEDIUM: [],
            SeverityLevel.LOW: []
        }
        
        for disc in discrepancies:
            severity = SeverityLevel(disc.severity) if hasattr(SeverityLevel, disc.severity.upper()) else SeverityLevel.MEDIUM
            categorized[severity].append(disc)
        
        return categorized
    
    def get_priority_discrepancies(
        self,
        discrepancies: List[Discrepancy],
        min_severity: SeverityLevel = SeverityLevel.MEDIUM
    ) -> List[Discrepancy]:
        """
        Get discrepancies above a minimum severity threshold.
        
        Args:
            discrepancies: List of discrepancies
            min_severity: Minimum severity level
        
        Returns:
            Filtered list of priority discrepancies
        """
        severity_levels = {
            SeverityLevel.CRITICAL: 3,
            SeverityLevel.HIGH: 2,
            SeverityLevel.MEDIUM: 1,
            SeverityLevel.LOW: 0
        }
        
        min_level = severity_levels.get(min_severity, 1)
        
        priority = []
        for disc in discrepancies:
            disc_severity = SeverityLevel(disc.severity) if hasattr(SeverityLevel, disc.severity.upper()) else SeverityLevel.MEDIUM
            if severity_levels.get(disc_severity, 0) >= min_level:
                priority.append(disc)
        
        return priority
