import os
import tempfile
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.QTA.QTA_review.qta_review_schema import (
    per_minute_qta_review_request, 
    per_minute_qta_review_response, 
    final_qta_review_request, 
    final_qta_review_response
)
from app.services.QTA.QTA_review.qta_review import QTAreview
from app.services.utils.convert_file import FileConverter
from app.services.utils.document_ocr import DocumentOCR
from typing import Optional, Dict, Any

router = APIRouter(prefix="/qta-review", tags=["qta-review"])
converter=FileConverter()
qta_service = QTAreview()
document_ocr = DocumentOCR()

@router.post("/per-minute-qta-review", response_model=per_minute_qta_review_response)
async def process_per_minute_review(
    transcribed_text: str = Form(...),
    existing_details: str = None  
):
    """
    Process per-minute QTA review with direct text input
    """
    try:
        if not transcribed_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcribed text provided"
            )
        
        input_data = per_minute_qta_review_request(
            transcribed_text=transcribed_text,
            existing_quality_review=existing_details  
        )
        
        result = qta_service.get_per_minute_summary(input_data)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing per-minute review: {str(e)}"
        )

@router.post("/final-qta-review", response_model=final_qta_review_response)
async def process_final_review(
    transcribed_text: str = Form(...),
    original_document: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    Process final QTA review using transcribed text, the original document (as string),
    and an optional uploaded reference document file.
    """
    try:
        if not transcribed_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcribed text must be provided."
            )

        if not original_document.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Original document must be provided as a string."
            )

        reference_document_text = "No reference document provided"
        temp_doc_paths = []

        if file and file.filename:
            file_ext = os.path.splitext(file.filename)[1].lower()

            if file_ext not in ['.pdf', '.docx', '.doc']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file_ext}. Please upload a PDF, DOCX, or DOC file."
                )

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    temp_input_path = temp_file.name
                    temp_doc_paths.append(temp_input_path)
                    content = await file.read()
                    temp_file.write(content)

                if file_ext in ['.docx', '.doc']:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as out_file:
                        temp_output_path = out_file.name
                        temp_doc_paths.append(temp_output_path)

                    if file_ext == '.docx':
                        converter.docx_to_pdf(temp_input_path, temp_output_path)
                    else:
                        converter.doc_to_pdf(temp_input_path, temp_output_path)

                    pdf_path = temp_output_path
                else:
                    pdf_path = temp_input_path

                try:
                    reference_document_text = document_ocr.extract_text(pdf_path)
                    if not reference_document_text:
                        reference_document_text = f"Could not extract text from {file.filename}"
                except Exception as e:
                    reference_document_text = f"Error extracting text from {file.filename}: {str(e)}"

            finally:
                for temp_path in temp_doc_paths:
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception as e:
                            print(f"Warning: Could not remove temporary file: {e}")

        input_data = final_qta_review_request(
            transcribed_text=transcribed_text,
            original_document=original_document,
            reference_document=reference_document_text
        )

        result = qta_service.get_final_summary(input_data)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing final review: {str(e)}"
        )





@router.post("/final-qta-review-repeat", response_model=final_qta_review_response)
async def process_final_review(
    existing_document: str = Form(...),
    existing_quality_review: str = Form(...),
    existing_change_summary: str = Form(...), 
    exists_review_summary: str = Form(...),
    user_changes: str = Form(...)
):
    try:
        existing_change_summary_dict = json.loads(existing_change_summary)
    except json.JSONDecodeError:
        existing_change_summary_dict = {}  

    result = qta_service.repeat_final_summary(
        existing_document,
        existing_quality_review,
        existing_change_summary_dict,
        exists_review_summary,
        user_changes
    )
    return result

