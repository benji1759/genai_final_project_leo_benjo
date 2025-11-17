"""
Multi-Agent System for Compliance Checking

This package contains specialized agents for document processing,
regulation retrieval, comparison, citation extraction, and report generation.
"""

from agents.base import BaseAgent, AgentMessage, AgentState
from agents.document_agent import DocumentAgent
from agents.regulation_agent import RegulationAgent
from agents.comparison_agent import ComparisonAgent
from agents.citation_agent import CitationAgent
from agents.report_agent import ReportAgent

__all__ = [
    "BaseAgent",
    "AgentMessage",
    "AgentState",
    "DocumentAgent",
    "RegulationAgent",
    "ComparisonAgent",
    "CitationAgent",
    "ReportAgent",
]
