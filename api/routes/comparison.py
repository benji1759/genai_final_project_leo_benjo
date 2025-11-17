"""
Comparison Routes

API endpoints for compliance analysis and comparison.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from api.schemas import (
    ComparisonRequest,
    AnalysisResponse,
    ComparisonResult,
    Discrepancy,
    ErrorResponse
)

from agent_orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/comparison", tags=["comparison"])

# Import from documents router
from api.routes.documents import _document_registry

# Store for analysis results
_analysis_results = {}

# Initialize orchestrator (singleton pattern)
_orchestrator = None


def get_orchestrator():
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(
            chroma_dir=os.getenv("CHROMA_DIR", "chroma_eu_laws"),
            verbose=False
        )
    return _orchestrator


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_compliance(
    request: ComparisonRequest,
    background_tasks: BackgroundTasks
):
    """
    Run compliance analysis on an uploaded document.
    
    This endpoint analyzes a policy document against selected EU regulations
    and returns detailed comparison results with citations.
    """
    # Validate document exists
    if request.document_id not in _document_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found"
        )
    
    doc_info = _document_registry[request.document_id]
    file_path = doc_info["file_path"]
    
    if not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document file not found: {file_path}"
        )
    
    try:
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Run analysis
        results = orchestrator.analyze_policy(
            file_path=file_path,
            regulation_types=request.regulation_types,
            document_id=request.document_id
        )
        
        # Store results
        _analysis_results[analysis_id] = results
        
        # Prepare response
        comparison = results.get("comparison_results", {})
        
        # Convert discrepancies to schema format
        discrepancies = []
        for disc in comparison.get("discrepancies", []):
            if isinstance(disc, dict):
                discrepancies.append(Discrepancy(
                    type=disc.get("type", "discrepancy"),
                    description=disc.get("description", str(disc)),
                    severity=disc.get("severity", "medium"),
                    regulation_article=disc.get("regulation_article")
                ))
            else:
                discrepancies.append(Discrepancy(
                    type="discrepancy",
                    description=str(disc),
                    severity="medium"
                ))
        
        comparison_result = ComparisonResult(
            compliance_score=comparison.get("compliance_score", 0),
            discrepancies=discrepancies,
            compliant_elements=comparison.get("compliant_elements", []),
            missing_requirements=comparison.get("missing_requirements", []),
            num_chunks_compared=comparison.get("num_chunks_compared", 0)
        )
        
        response = AnalysisResponse(
            analysis_id=analysis_id,
            document_id=request.document_id,
            status="completed",
            timestamp=datetime.now(),
            comparison_results=comparison_result,
            citations=results.get("citations", {}),
            report_path=results.get("report", {}).get("report_path")
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during analysis: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    """Get analysis results by ID."""
    if analysis_id not in _analysis_results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )
    
    results = _analysis_results[analysis_id]
    
    # Convert to response format
    comparison = results.get("comparison_results", {})
    
    discrepancies = []
    for disc in comparison.get("discrepancies", []):
        if isinstance(disc, dict):
            discrepancies.append(Discrepancy(
                type=disc.get("type", "discrepancy"),
                description=disc.get("description", str(disc)),
                severity=disc.get("severity", "medium"),
                regulation_article=disc.get("regulation_article")
            ))
        else:
            discrepancies.append(Discrepancy(
                type="discrepancy",
                description=str(disc),
                severity="medium"
            ))
    
    comparison_result = ComparisonResult(
        compliance_score=comparison.get("compliance_score", 0),
        discrepancies=discrepancies,
        compliant_elements=comparison.get("compliant_elements", []),
        missing_requirements=comparison.get("missing_requirements", []),
        num_chunks_compared=comparison.get("num_chunks_compared", 0)
    )
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        document_id=results.get("document_info", {}).get("document_id", "unknown"),
        status="completed",
        timestamp=datetime.now(),
        comparison_results=comparison_result,
        citations=results.get("citations", {}),
        report_path=results.get("report", {}).get("report_path")
    )


@router.get("/")
async def list_analyses():
    """List all analysis results."""
    return {
        "analyses": list(_analysis_results.keys()),
        "count": len(_analysis_results)
    }
