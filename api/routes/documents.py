"""
Document Routes

API endpoints for document upload and management.
"""

import os
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from api.schemas import DocumentUploadResponse, ErrorResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Store for uploaded documents (in production, use a database)
DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True, parents=True)

# In-memory document registry
_document_registry = {}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Policy document file (PDF, DOCX, or TXT)")
):
    """
    Upload a policy document for compliance analysis.
    
    Supported formats: PDF, DOCX, TXT
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Save file
        file_path = DOCUMENTS_DIR / f"{document_id}{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Register document
        _document_registry[document_id] = {
            "id": document_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "file_type": file_ext[1:].upper(),
            "size": len(content)
        }
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_type=file_ext[1:].upper(),
            status="uploaded",
            message="Document uploaded successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document information."""
    if document_id not in _document_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    return _document_registry[document_id]


@router.get("/")
async def list_documents():
    """List all uploaded documents."""
    return {
        "documents": list(_document_registry.values()),
        "count": len(_document_registry)
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    if document_id not in _document_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    doc_info = _document_registry[document_id]
    file_path = Path(doc_info["file_path"])
    
    if file_path.exists():
        file_path.unlink()
    
    del _document_registry[document_id]
    
    return {"message": f"Document {document_id} deleted successfully"}
