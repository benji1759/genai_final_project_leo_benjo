"""
FastAPI Main Application

REST API server for policy compliance checking.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from api.routes import documents, comparison, reports
from api.schemas import RegulationListResponse

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="EU Policy Compliance Checker API",
    description="REST API for analyzing policy documents against EU regulations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(comparison.router)
app.include_router(reports.router)


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint."""
    return {
        "message": "EU Policy Compliance Checker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/regulations", response_model=RegulationListResponse)
async def list_regulations():
    """
    List available EU regulations that can be checked.
    
    Returns a list of regulation types and their descriptions.
    """
    regulations = {
        "GDPR": "General Data Protection Regulation (EU) 2016/679",
        "AI Act": "Artificial Intelligence Act (EU) 2024/...",
        "NIS2": "Network and Information Systems Directive 2 (EU) 2022/2555",
        "DSA": "Digital Services Act (EU) 2022/2065",
        "DMA": "Digital Markets Act (EU) 2022/1925"
    }
    
    return RegulationListResponse(
        regulations=list(regulations.keys()),
        descriptions=regulations
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "status": "healthy" if api_key else "unhealthy",
        "api_key_configured": bool(api_key),
        "message": "API is operational" if api_key else "OPENAI_API_KEY not configured"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
