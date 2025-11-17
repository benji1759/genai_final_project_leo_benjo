"""
API Schemas

Pydantic models for request/response validation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    file_type: str
    status: str
    message: str


class ComparisonRequest(BaseModel):
    """Request model for compliance analysis."""
    document_id: str
    regulation_types: Optional[List[str]] = Field(
        default=None,
        description="List of regulation types to check (e.g., ['GDPR', 'AI Act'])"
    )


class Discrepancy(BaseModel):
    """Discrepancy model."""
    type: str
    description: str
    severity: str
    regulation_article: Optional[str] = None


class Citation(BaseModel):
    """Citation model."""
    reference: str
    regulation_type: Optional[str] = None
    context: Optional[str] = None


class ComparisonResult(BaseModel):
    """Comparison result model."""
    compliance_score: int = Field(..., ge=0, le=100)
    discrepancies: List[Discrepancy]
    compliant_elements: List[str]
    missing_requirements: List[str]
    num_chunks_compared: int


class AnalysisResponse(BaseModel):
    """Response model for compliance analysis."""
    analysis_id: str
    document_id: str
    status: str
    timestamp: datetime
    comparison_results: ComparisonResult
    citations: Dict[str, Any]
    report_path: Optional[str] = None


class RegulationListResponse(BaseModel):
    """Response model for available regulations."""
    regulations: List[str]
    descriptions: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    status_code: int
