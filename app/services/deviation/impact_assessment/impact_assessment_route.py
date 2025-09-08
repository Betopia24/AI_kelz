#!/usr/bin/env python3
"""
Impact Assessment Router Module
Endpoint to produce impact assessment fields only, based on prior incident analysis and optional document content.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Response
from typing import Optional
import os
import json
import tempfile
import re

from app.services.deviation.impact_assessment.impact_assessment import ImpactAssessmentManager


def register_impact_assessment_routes(router: APIRouter):
    manager = ImpactAssessmentManager()

    @router.post("/deviation/impact-assessment", tags=["deviation"])
    async def impact_assessment(
        analysis: str = Form(..., description="Stringified JSON or strict-text response from /incident/analyze/audio"),
        files: Optional[list[UploadFile]] = File(None)
    ):
        try:
            # Validate and extract text from all provided files
            extracted_texts = []
            if files:
                valid_doc_extensions = ['.pdf', '.docx', '.txt']
                for file in files:
                    if file and hasattr(file, 'filename') and file.filename:
                        file_content = await file.read()
                        if not file.filename.strip() or not file_content:
                            continue
                        file_ext = os.path.splitext(file.filename)[1].lower()
                        if file_ext not in valid_doc_extensions:
                            raise HTTPException(status_code=400, detail=f"Unsupported document file format: {file_ext}")
                        if len(file_content) > 25 * 1024 * 1024:
                            raise HTTPException(status_code=400, detail="Document file too large. Maximum size is 25MB.")
                        text = manager.extract_text_from_document(file_content, file.filename)
                        if text:
                            extracted_texts.append(text)
            # Merge all extracted texts
            merged_text = "\n\n".join(extracted_texts) if extracted_texts else None
            # Process assessment
            output_text = manager.generate_assessment_text(analysis, merged_text)
            return Response(content=output_text, media_type="text/plain")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impact assessment failed: {str(e)}")


