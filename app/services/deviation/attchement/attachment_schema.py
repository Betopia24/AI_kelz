from pydantic import BaseModel
from typing import Optional, List

class DocumentAnalysis(BaseModel):
    AI_suggested_Title: str
    Batch_records: str
    SOP_s: str
    Forms: str
    Interviews: str
    Logbooks: str
    Email_references: str
    Certificates: str

class FileWithVoiceTitle(BaseModel):
    file_type: str
    display_name: str
    filename: str
    voice_title: str
    category: str
    confidence: Optional[int] = None
    reasoning: Optional[str] = None
    content_evidence: Optional[str] = None  # Why this category was chosen or AI reasoning

class EnhancedFileAnalysisResponse(BaseModel):
    AI_suggested_Title: str
    user_audio: Optional[str] = None
    files: List[FileWithVoiceTitle]

# Legacy schema for backward compatibility
class FileExtractResponse(BaseModel):
    status: str
    filename: str
    file_type: str
    extracted_content: str
    document_analysis: DocumentAnalysis
    message: str

# Internal models for processing
class FileMapping(BaseModel):
    filename: str
    category: str
    voice_title: str
    content_evidence: Optional[str] = None

class CategorizationResult(BaseModel):
    AI_suggested_Title: str
    file_mappings: List[FileMapping]