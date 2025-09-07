from fastapi import APIRouter, UploadFile, File, HTTPException, Response
import tempfile, os, json
from typing import List

from app.services.deviation.attchement.attachment import AIDocumentAnalysisService
from app.services.deviation.attchement.attachment_schema import EnhancedFileAnalysisResponse

router = APIRouter()

@router.post("/attachment/file-analyze", tags=["deviation"], response_model=EnhancedFileAnalysisResponse)
async def analyze_file(
    files: List[UploadFile] = File(..., description="Upload one or more files under 'files'"),
    voice_file: UploadFile = File(None)
):
    """
    Accept multiple document files and an optional audio file, then return a JSON response:
    
    AUTOMATIC FILE CATEGORIZATION:
    The AI will automatically categorize each file into one of these predefined types based on content analysis:
    - Batch_records: Manufacturing batch documentation, production records, lot records
    - SOP_s: Standard Operating Procedures, process instructions, protocols
    - Forms: Templates, blank forms, checklists, data collection sheets
    - Interviews: Interview transcripts, meeting notes, personnel discussions
    - Logbooks: Daily logs, maintenance records, equipment logs, shift records
    - Email_references: Email communications, correspondence, notifications
    - Certificates: Training certificates, qualification documents, compliance certificates
    
    VOICE TITLE MATCHING:
    User can provide titles via voice audio which will be matched to appropriate files.
    
    RESPONSE FORMAT:
    {
      "AI_suggested_Title": "<overall title for document set>",
      "user_audio": "<transcription if provided>",
      "files": [
        {
          "file_type": "<auto-detected category>",
          "display_name": "<user_voice_title> - <filename>", 
          "filename": "<original_filename>",
          "voice_title": "<title_from_voice>",
          "category": "<document_category>",
          "confidence": <optional_confidence>,
          "reasoning": "<optional_reasoning>"
        }
      ]
    }
    """
    # Initialize the AI Document Analysis Service (falls back to rule-based if API key missing)
    service = AIDocumentAnalysisService(openai_api_key=os.getenv("OPENAI_API_KEY", ""))

    # Optional voice file handling (transcribed later by service)
    user_audio: str = ""
    voice_tmp = None
    if voice_file is not None:
        vcontent = await voice_file.read()
        if vcontent:
            vsuffix = os.path.splitext(voice_file.filename)[1] or ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=vsuffix) as vtmp:
                vtmp.write(vcontent)
                voice_tmp = vtmp.name
            
            # FIXED: Transcribe the voice immediately after saving
            try:
                user_audio = service.voice_transcriber.transcribe_audio(voice_tmp) or ""
            except Exception as e:
                print(f"Voice transcription failed: {e}")
                user_audio = ""

    # Validate there is at least one file
    if not files or len(files) == 0:
        # Clean up voice temp file if created
        if voice_tmp and os.path.exists(voice_tmp):
            try:
                os.unlink(voice_tmp)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Persist uploaded files to temporary paths for processing
    temp_files = []  # [{"path": str, "original_name": str}]
    for f in [f for f in files if f is not None]:
        if not getattr(f, 'filename', None):
            continue
        content = await f.read()
        if not content:
            continue
        suffix = os.path.splitext(f.filename)[1] or ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
            tf.write(content)
            temp_files.append({
                "path": tf.name,
                "original_name": f.filename
            })

    # If no valid files were saved, return default structure
    if not temp_files:
        # Cleanup voice tmp
        if voice_tmp and os.path.exists(voice_tmp):
            try:
                os.unlink(voice_tmp)
            except Exception:
                pass

        response_data = {
            "AI_suggested_Title": "Not found in document",
            "files": []
        }
        if user_audio:
            response_data["user_audio"] = user_audio
        for f in [f for f in files if f is not None]:
            fname = getattr(f, 'filename', '') or ''
            if fname:
                response_data["files"].append({
                    "file_type": "Forms",
                    "display_name": f"Unknown Title - {fname}",
                    "filename": fname,
                    "voice_title": "Unknown Title",
                    "category": "Forms"
                })
        return Response(
            content=json.dumps(response_data, indent=2, ensure_ascii=False),
            media_type="application/json"
        )

    # Prepare inputs for the service
    file_paths = [t["path"] for t in temp_files]
    temp_to_original = {os.path.basename(t["path"]): t["original_name"] for t in temp_files}

    # Process files with optional voice input using the AI/Rule-based service
    try:
        result = service.process_files_with_voice_input(file_paths, audio_file_path=voice_tmp)
    finally:
        # Cleanup all temporary files (documents and voice)
        for t in temp_files:
            if t["path"] and os.path.exists(t["path"]):
                try:
                    os.unlink(t["path"])
                except Exception:
                    pass
        if voice_tmp and os.path.exists(voice_tmp):
            try:
                os.unlink(voice_tmp)
            except Exception:
                pass

    # If processing failed, provide a fallback response
    if not isinstance(result, dict) or "error" in result:
        response_data = {
            "AI_suggested_Title": "Not found in document",
            "files": []
        }
        # FIXED: Include user_audio even in fallback
        if user_audio:
            response_data["user_audio"] = user_audio
        for t in temp_files:
            fname = t["original_name"]
            if fname:
                response_data["files"].append({
                    "file_type": "Forms",
                    "display_name": f"Unknown Title - {fname}",
                    "filename": fname,
                    "voice_title": "Unknown Title",
                    "category": "Forms"
                })
        return Response(
            content=json.dumps(response_data, indent=2, ensure_ascii=False),
            media_type="application/json"
        )

    # Build the success response using AI/Rule-based mapping
    response_data = {
        "AI_suggested_Title": result.get("AI_suggested_Title", "Document Collection"),
        "files": []
    }

    # FIXED: Prioritize the directly transcribed user_audio over processing_summary
    # Include transcribed voice text if available
    processing_summary = result.get("processing_summary", {}) if isinstance(result, dict) else {}
    service_audio = processing_summary.get("voice_transcription", "") if isinstance(processing_summary, dict) else ""
    
    # Use the directly transcribed audio first, fallback to service transcription
    final_audio = user_audio if user_audio and user_audio.strip() else service_audio
    if final_audio and final_audio != "No voice input provided":
        response_data["user_audio"] = final_audio

    # Map temp filenames back to original filenames
    file_mappings = result.get("file_mappings", []) if isinstance(result, dict) else []
    covered = set()
    for m in file_mappings:
        temp_name = m.get("filename", "")
        original_name = temp_to_original.get(temp_name, temp_name)
        category = m.get("category", "Forms")
        voice_title = m.get("voice_title", "User Title Not Specified")
        file_entry = {
            "file_type": category,
            "display_name": f"{voice_title} - {original_name}",
            "filename": original_name,
            "voice_title": voice_title,
            "category": category
        }
        # Optional AI fields
        if "confidence" in m and m["confidence"] is not None:
            file_entry["confidence"] = m["confidence"]
        if "reasoning" in m and m["reasoning"]:
            file_entry["reasoning"] = m["reasoning"]
        if "content_evidence" in m and m["content_evidence"]:
            file_entry["content_evidence"] = m["content_evidence"]

        response_data["files"].append(file_entry)
        covered.add(original_name)

    # Ensure every uploaded file is represented even if mapping missed it
    for t in temp_files:
        original_name = t["original_name"]
        if original_name not in covered:
            response_data["files"].append({
                "file_type": "Forms",
                "display_name": f"User Title Not Specified - {original_name}",
                "filename": original_name,
                "voice_title": "User Title Not Specified",
                "category": "Forms"
            })

    return Response(
        content=json.dumps(response_data, indent=2, ensure_ascii=False),
        media_type="application/json"
    )