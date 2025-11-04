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
    transcribed_text: str = Form(...),
    files: list[UploadFile] = File(...)
):
    """
    Process final QTA revision with transcribed text and document processing
    """

    try:
        if not transcribed_text or not transcribed_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcribed text must be provided"
            )

        if len(files) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exactly 2 document files must be provided"
            )

        client_file = None
        user_file = None

        for file in files:
            if not file.filename:
                continue
            filename_lower = file.filename.lower()

            if 'client' in filename_lower:
                client_file = file
            elif 'user' in filename_lower:
                user_file = file

        if not client_file or not user_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload files with proper names. Filenames should contain 'client' and 'user' respectively."
            )

        temp_doc_paths = []

        try:
            client_ext = os.path.splitext(client_file.filename)[1].lower()
            if client_ext not in ['.pdf', '.docx', '.doc']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type for client file: {client_ext}. Please upload a PDF, DOCX, or DOC file."
                )

            with tempfile.NamedTemporaryFile(delete=False, suffix=client_ext) as temp_file:
                temp_client_input_path = temp_file.name
                temp_doc_paths.append(temp_client_input_path)
                content = await client_file.read()
                temp_file.write(content)

            if client_ext in ['.docx', '.doc']:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as out_file:
                    temp_client_output_path = out_file.name
                    temp_doc_paths.append(temp_client_output_path)

                try:
                    if client_ext == '.docx':
                        converter.docx_to_pdf(temp_client_input_path, temp_client_output_path)
                    else:
                        converter.doc_to_pdf(temp_client_input_path, temp_client_output_path)

                    client_pdf_path = temp_client_output_path
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to convert client document to PDF: {str(e)}"
                    )
            else:
                client_pdf_path = temp_client_input_path

            try:
                client_document_text = document_ocr.extract_text(client_pdf_path)
                if not client_document_text:
                    client_document_text = f"Could not extract text from {client_file.filename}"
            except Exception as e:
                client_document_text = f"Error extracting text from {client_file.filename}: {str(e)}"

            user_ext = os.path.splitext(user_file.filename)[1].lower()
            if user_ext not in ['.pdf', '.docx', '.doc']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type for user file: {user_ext}. Please upload a PDF, DOCX, or DOC file."
                )

            with tempfile.NamedTemporaryFile(delete=False, suffix=user_ext) as temp_file:
                temp_user_input_path = temp_file.name
                temp_doc_paths.append(temp_user_input_path)
                content = await user_file.read()
                temp_file.write(content)

            if user_ext in ['.docx', '.doc']:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as out_file:
                    temp_user_output_path = out_file.name
                    temp_doc_paths.append(temp_user_output_path)

                try:
                    if user_ext == '.docx':
                        converter.docx_to_pdf(temp_user_input_path, temp_user_output_path)
                    else:
                        converter.doc_to_pdf(temp_user_input_path, temp_user_output_path)

                    user_pdf_path = temp_user_output_path
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to convert user document to PDF: {str(e)}"
                    )
            else:
                user_pdf_path = temp_user_input_path

            try:
                user_document_text = document_ocr.extract_text(user_pdf_path)
                if not user_document_text:
                    user_document_text = f"Could not extract text from {user_file.filename}"
            except Exception as e:
                user_document_text = f"Error extracting text from {user_file.filename}: {str(e)}"

            input_data = final_qta_revision_request(
                transcribed_text=transcribed_text,
                client_document=client_document_text,
                user_document=user_document_text
            )

            result = qta_service.get_final_summary(input_data)
            return result

        finally:
            for temp_path in temp_doc_paths:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as e:
                        print(f"Warning: Could not remove temporary document file: {e}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing final revision: {str(e)}"
        )


@router.post("/final-qta-revision-repeat", response_model=final_qta_revision_response)
async def process_final_revision(request:repeat_qta_revision_request):
    try:
        result = qta_service.repeat_final_summary(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing repeat final revision: {str(e)}"
        )