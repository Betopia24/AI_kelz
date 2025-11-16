import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from fastapi.responses import JSONResponse
from app.services.QTA.QTA_revision.QTA_revision_schema import (
    per_minute_qta_revision_request, 
    per_minute_qta_revision_response, 
    final_qta_revision_request, 
    final_qta_revision_response,
    repeat_qta_revision_request
)
from app.services.QTA.QTA_revision.QTA_revision import QTARevision
from app.services.utils.convert_file import FileConverter
from app.services.utils.document_ocr import DocumentOCR
from typing import Dict, Any

router = APIRouter(prefix="/qta-revision", tags=["qta-revision"])
converter=FileConverter()
qta_service = QTARevision()
document_ocr = DocumentOCR()

@router.post("/per-minute-qta-revision", response_model=per_minute_qta_revision_response)
async def process_per_minute_revision(request: per_minute_qta_revision_request):
    """
    Process per-minute QTA revision with direct text input
    """
    try:
        result = qta_service.get_per_minute_summary(request)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing per-minute revision: {str(e)}"
        )

@router.post("/final-qta-revision", response_model=final_qta_revision_response)
async def process_final_revision(
     request: final_qta_revision_request
):
    """
    Process final QTA revision with transcribed text and document processing
    """
    try:
        response = qta_service.get_final_summary(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing final revision: {str(e)}"
        )


@router.post("/final-qta-revision-repeat", response_model=final_qta_revision_response)
async def process_final_revision_repeat(request: repeat_qta_revision_request):
    try:
        result = qta_service.repeat_final_summary(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing repeat final revision: {str(e)}"
        )