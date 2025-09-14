#!/usr/bin/env python3
"""
Quality Review Router
FastAPI router for quality review endpoints
"""

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path


from app.services.deviation.quality_review.quality_review import QualityReviewer
from app.services.deviation.quality_review.quality_review_schema import VoiceQualityReviewResponse

# Create router
router = APIRouter()


quality_reviewer = QualityReviewer()



@router.post(
    "/quality-review/",
    tags=["deviation"],
    summary="Quality Review",
    description="Upload one or more documents and/or voice files, and get a quality/SME review with extracted and transcribed text."
)
async def quality_review(
    files: Optional[list[UploadFile]] = File(None),
    voice_files: Optional[list[UploadFile]] = File(None),
    transcribed_text: str = Form(""),
    action_summary: str = Form("")
):
    """
    Quality Review endpoint with multi-file support:
    - files: Optional list of document files (pdf, docx, doc, txt, rtf, etc)
    - voice_files: Optional list of audio files (mp3, wav, m4a, mp4, webm, ogg, flac, etc)
    - transcribed_text: Optional direct text input
    - action_summary: Optional summary or checklist for review
    Returns review summary, transcribed text, and extracted document text for each file.
    """
    import uuid
    from app.services.utils.transcription import transcribe_audio
    from app.services.utils.document_ocr import DocumentOCR
    temp_dir = tempfile.gettempdir()
    responses = []
    temp_paths = []
    try:
        # Handle multiple voice files
        if voice_files:
            for voice_file in voice_files:
                file_extension = os.path.splitext(voice_file.filename)[1]
                temp_path = os.path.join(temp_dir, f"voice_{uuid.uuid4().hex}{file_extension}")
                content = await voice_file.read()
                with open(temp_path, 'wb') as f:
                    f.write(content)
                transcribed_text_result = transcribe_audio(temp_path)
                if not transcribed_text_result:
                    responses.append({
                        "status": "error",
                        "filename": voice_file.filename,
                        "message": "Transcription failed or returned empty text."
                    })
                    temp_paths.append(temp_path)
                    continue
                result = quality_reviewer.process_voice_for_quality_review(temp_path)
                responses.append({
                    "status": "success",
                    "filename": voice_file.filename,
                    "transcribed_text": transcribed_text_result,
                    "quality_review": result.get("quality_review"),
                    "sme_review": result.get("sme_review"),
                    "message": result.get("message", "Quality review completed successfully")
                })
                temp_paths.append(temp_path)
        # Handle multiple document files
        if files:
            for file in files:
                doc_extension = os.path.splitext(file.filename)[1]
                doc_temp_path = os.path.join(temp_dir, f"review_{uuid.uuid4().hex}{doc_extension}")
                doc_content = await file.read()
                with open(doc_temp_path, 'wb') as doc_f:
                    doc_f.write(doc_content)
                document_ocr = DocumentOCR()
                processed_document_text = document_ocr.process_file(doc_temp_path)
                responses.append({
                    "status": "success",
                    "filename": file.filename,
                    "extracted_document_text": processed_document_text,
                    "message": "Document extracted successfully."
                })
                temp_paths.append(doc_temp_path)
        # If direct text input is provided
        if transcribed_text and not (files or voice_files):
            responses.append({
                "status": "success",
                "filename": None,
                "transcribed_text": transcribed_text,
                "message": "Direct text input processed."
            })
        if not responses:
            responses.append({"status": "error", "message": "No input provided."})
        return {"results": responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality review error: {str(e)}")
    finally:
        for p in temp_paths:
            if p and os.path.exists(p):
                os.unlink(p)



