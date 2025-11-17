"""
Report Routes

API endpoints for report generation and download.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.routes.comparison import _analysis_results

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{analysis_id}/pdf")
async def download_pdf_report(analysis_id: str):
    """
    Download PDF compliance report for an analysis.
    
    Returns the generated PDF report file.
    """
    if analysis_id not in _analysis_results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )
    
    results = _analysis_results[analysis_id]
    report_path = results.get("report", {}).get("report_path")
    
    if not report_path or not Path(report_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Report file not found. Analysis may not have generated a report."
        )
    
    return FileResponse(
        path=report_path,
        filename=Path(report_path).name,
        media_type="application/pdf"
    )


@router.get("/{analysis_id}/json")
async def download_json_report(analysis_id: str):
    """Download analysis results as JSON."""
    if analysis_id not in _analysis_results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )
    
    import json
    results = _analysis_results[analysis_id]
    
    from fastapi.responses import JSONResponse
    return JSONResponse(content=results)
