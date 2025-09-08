#!/usr/bin/env python3
"""
Impact Assessment Schemas
Pydantic models for impact assessment features.
"""
from pydantic import BaseModel, Field
from typing import Optional

class ImpactAssessmentRequest(BaseModel):
    """Optional JSON-request schema (not used by multipart endpoint, but handy for docs/testing)."""
    analysis: str = Field(..., description="Stringified JSON or strict-text response from /incident/analyze/audio")
    document_text: Optional[str] = Field(None, description="Optional pre-extracted document text if OCR not used")

class ImpactAssessmentTextResponse(BaseModel):
    """A text/plain response body represented as a string for OpenAPI docs."""
    content: str = Field(..., description="Eight-line impact assessment text in strict format")
