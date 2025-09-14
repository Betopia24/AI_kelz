from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from .qta_review import Review, process_review_with_file
from .qta_review_schema import review_resonse, review_request
import tempfile
import os
import shutil
import uuid
from app.services.utils.transcription import transcribe_audio

router = APIRouter()
review = Review()

@router.post("/review")
async def get_review(
    files: list[UploadFile] = File(None),
    voice_files: list[UploadFile] = File(None),
    transcribed_text: str = Form(""),
    action_summary: str = Form(...)
):
    try:
        import uuid
        temp_dir = tempfile.gettempdir()
        responses = []
        # Handle multiple voice files
        if voice_files:
            for voice_file in voice_files:
                file_extension = os.path.splitext(voice_file.filename)[1]
                temp_path = os.path.join(temp_dir, f"voice_{uuid.uuid4().hex}{file_extension}")
                try:
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
                        continue
                    request = review_request(
                        transcribed_text=transcribed_text_result,
                        processed_document_text=None,
                        action_summary=action_summary
                    )
                    summary = review.get_summary(request)
                    responses.append({
                        "status": "success",
                        "filename": voice_file.filename,
                        "transcribed_text": transcribed_text_result,
                        "review_summary": summary.summary if hasattr(summary, "summary") else summary
                    })
                finally:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception:
                        pass
        # Handle multiple document files
        if files:
            for file in files:
                file_extension = os.path.splitext(file.filename)[1]
                temp_path = os.path.join(temp_dir, f"review_{uuid.uuid4().hex}{file_extension}")
                try:
                    content = await file.read()
                    with open(temp_path, 'wb') as f:
                        f.write(content)
                    processed_document_text = review.process_document(temp_path)
                    response = process_review_with_file(
                        temp_path,
                        transcribed_text,
                        action_summary
                    )
                    responses.append({
                        "status": "success",
                        "filename": file.filename,
                        "extracted_document_text": processed_document_text,
                        "review_summary": response.summary if hasattr(response, "summary") else response,
                        "transcribed_text": transcribed_text
                    })
                finally:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception:
                        pass
        # No file uploads, just text
        if not files and not voice_files:
            request = review_request(
                transcribed_text=transcribed_text,
                processed_document_text=None,
                action_summary=action_summary
            )
            summary = review.get_summary(request)
            responses.append({
                "review_summary": summary.summary if hasattr(summary, "summary") else summary,
                "transcribed_text": transcribed_text
            })
        return {"results": responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
