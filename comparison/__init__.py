"""
Compliance Comparison Module

Contains core comparison logic, discrepancy detection, and severity assessment.
"""

from comparison.comparator import ComplianceComparator
from comparison.discrepancy_detector import DiscrepancyDetector
from comparison.severity_assessor import SeverityAssessor

__all__ = [
    "ComplianceComparator",
    "DiscrepancyDetector",
    "SeverityAssessor",
]
