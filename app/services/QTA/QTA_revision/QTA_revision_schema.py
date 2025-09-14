from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VoiceRevisionRequest(BaseModel):
    """Request model for voice revision processing"""
    pass  # File will be handled in route as UploadFile

class VoiceRevisionResponse(BaseModel):
    """Response model for voice revision processing"""
    status: str
    message: str
    transcribed_text_as_bullet_point: List[str]
    summary: str
    processed_document_text: Optional[str] = None

class AIUpdateDocumentRequest(BaseModel):
    summary: str
    processed_document_text: str

class AIUpdateDocumentResponse(BaseModel):
    updated_text: str

class ErrorResponse(BaseModel):
    """Error response model"""
    status: str
    message: str
    error_code: Optional[str] = None