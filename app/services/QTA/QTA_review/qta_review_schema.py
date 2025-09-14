from pydantic import BaseModel
from typing import Optional
class review_request(BaseModel):
    transcribed_text:str
    processed_document_text: Optional[str] = None
    action_summary:str
class review_resonse(BaseModel):
    summary:str
    
