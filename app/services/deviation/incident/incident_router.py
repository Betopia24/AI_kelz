#!/usr/bin/env python3
"""
Simplified Incident Router Module
Single endpoint for incident analysis with clean JSON response
"""

from fastapi import File, UploadFile, HTTPException, Depends, Response
from typing import Optional
import tempfile
import os

from app.services.deviation.incident.incident import IncidentManager


def register_incident_routes(router):
    incident_manager = IncidentManager()

    @router.post("/incident/analyze/audio", tags=["deviation"])
    async def analyze_incident(
        audio: Optional[UploadFile] = File(None),
        file: Optional[UploadFile] = File(None),
        manager: IncidentManager = Depends(lambda: incident_manager)
    ):
        """
        Analyze incident from audio and/or document file and return structured JSON response

        Args:
            audio: Audio file upload (optional)
            file: Document file upload (optional)
            manager: Incident manager instance

        Returns:
            dict: Clean JSON response with incident analysis
        """
        try:
            valid_audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4']
            valid_doc_extensions = ['.pdf', '.docx', '.txt']
            valid_extensions = valid_audio_extensions + valid_doc_extensions

            audio_text = None
            file_text = None
            filenames = []

            # Process audio if provided and not empty
            print("DEBUG: audio=", audio)
            print("DEBUG: file=", file)
            if audio and hasattr(audio, 'filename') and audio.filename:
                audio_content = await audio.read()
                print("DEBUG: audio.filename=", audio.filename)
                print("DEBUG: len(audio_content)=", len(audio_content))
                if not audio.filename.strip() or not audio_content:
                    audio = None  # Treat as not provided
                else:
                    audio_ext = os.path.splitext(audio.filename)[1].lower()
                    print("DEBUG: audio_ext=", audio_ext)
                    if audio_ext not in valid_audio_extensions:
                        raise HTTPException(status_code=400, detail=f"Unsupported audio file format: {audio_ext}")
                    if len(audio_content) > 25 * 1024 * 1024:
                        raise HTTPException(status_code=400, detail="Audio file too large. Maximum size is 25MB.")
                    result_audio = manager.process_uploaded_file(audio_content, audio.filename)
                    if result_audio.success and result_audio.transcription:
                        audio_text = result_audio.transcription
                    filenames.append(audio.filename)


            # Process document if provided and not empty
            if file and hasattr(file, 'filename') and file.filename:
                file_content = await file.read()
                print("DEBUG: file.filename=", file.filename)
                print("DEBUG: len(file_content)=", len(file_content))
                if not file.filename.strip() or not file_content:
                    file = None  # Treat as not provided
                else:
                    file_ext = os.path.splitext(file.filename)[1].lower()
                    print("DEBUG: file_ext=", file_ext)
                    if file_ext not in valid_doc_extensions:
                        raise HTTPException(status_code=400, detail=f"Unsupported document file format: {file_ext}")
                    if len(file_content) > 25 * 1024 * 1024:
                        raise HTTPException(status_code=400, detail="Document file too large. Maximum size is 25MB.")
                    result_doc = manager.process_uploaded_document(file_content, file.filename)
                    if result_doc.success and result_doc.transcription:
                        file_text = result_doc.transcription
                    filenames.append(file.filename)

            # Build strict text output per prompt, always returning text/plain
            def _format_strict_output(data: dict) -> str:
                def _v(k: str) -> str:
                    val = data.get(k)
                    if isinstance(val, str):
                        val = val.strip()
                    return val if val else "Not specified"
                lines = [
                    "===ANALYSIS START===",
                    f"INCIDENT_TITLE: {_v('title')}",
                    f"BACKGROUND: {_v('background')}",
                    f"WHO: {_v('who')}",
                    f"WHAT: {_v('what')}",
                    f"WHERE: {_v('where')}",
                    f"IMMEDIATE_ACTION: {_v('immediate_action')}",
                    f"QUALITY_CONCERNS: {_v('quality_concerns')}",
                    f"QUALITY_CONTROLS: {_v('quality_controls')}",
                    f"RCA_TOOL: {_v('rca_tool')}",
                    f"EXPECTED_INTERIM_ACTION: {_v('expected_interim_action')}",
                    f"CAPA: {_v('capa')}",
                    f"ATTENDEES: {_v('attendees')}",
                ]
                return "\n".join(lines)

            text_to_analyze = None
            if audio_text and file_text:
                text_to_analyze = (audio_text or "").strip() + "\n\n" + (file_text or "").strip()
            elif audio_text:
                text_to_analyze = (audio_text or "").strip()
            elif file_text:
                text_to_analyze = (file_text or "").strip()

            if not text_to_analyze:
                return Response(content=_format_strict_output({}), media_type="text/plain")

            # Use the analyzer directly to get all fields including background and attendees
            ai_data = manager.analyzer.analyze_incident(text_to_analyze) or {}
            # Normalize keys that might be missing
            for k in ["title","background","who","what","where","immediate_action","quality_concerns","quality_controls","rca_tool","expected_interim_action","capa","attendees"]:
                ai_data.setdefault(k, "Not specified")
            return Response(content=_format_strict_output(ai_data), media_type="text/plain")

        except HTTPException:
            raise
        except Exception as e:
            return {
                "status": "error",
                "filename": ", ".join(filenames) if filenames else "unknown",
                "incident_description": "",
                "headline": "",
                "incident_data": {
                    "title": "",
                    "who": "",
                    "what": "",
                    "where": "",
                    "immediate_action": "",
                    "quality_concerns": "",
                    "quality_controls": "",
                    "rca_tool": "",
                    "expected_interim_action": "",
                    "capa": ""
                },
                "message": f"Error processing file(s): {str(e)}"
            }
