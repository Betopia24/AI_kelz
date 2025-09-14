from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends
from fastapi.responses import JSONResponse
from app.services.deviation.Inverstigation_modify.Inverstigation_modify_schema import InvestigationModifyInput
from app.services.deviation.Inverstigation_modify.Inverstigation_modify import generate_modified_investigation
from app.services.utils.transcription import transcribe_audio
import json
import os
import tempfile

router = APIRouter()

@router.post("/investigation-modify-with-audio", tags=["deviation"])
async def investigation_modify_with_audio(
    investigation_response: str = Body(..., embed=True, description="Original investigation response (JSON string)"),
    instruction_audio: UploadFile = File(..., description="Audio file with modify instruction")
):
    """
    Takes the original investigation response and a voice instruction (audio file),
    transcribes the instruction, and returns the AI-modified response.
    """
    try:
        response_dict = json.loads(investigation_response)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON for investigation_response.")

    # Transcribe audio to text
    temp_file_path = None
    try:
        # Read uploaded audio content and save to a temporary file
        content = await instruction_audio.read()
        if not content:
            raise ValueError("Empty audio file")
        suffix = os.path.splitext(instruction_audio.filename)[1] or ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_file_path = tmp.name
        # Transcribe using local transcriber that expects a file path
        instruction_text = transcribe_audio(temp_file_path)
        if not instruction_text:
            raise ValueError("Transcription returned empty result")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {exc}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    # Get the modified response from the system
    try:
        modified_response = generate_modified_investigation(response_dict, instruction_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI modification failed: {exc}")

    return JSONResponse(status_code=200, content=modified_response)
