from pydantic import BaseModel
from typing import Optional,Dict,Any


class per_minute_qta_revision_request(BaseModel):
    transcribed_text:str
    existing_changed_details:Optional[str]=None
    existing_action_summary:Optional[str]=None

class per_minute_qta_revision_response(BaseModel):
    changed_details:str
    action_summary:str
class final_qta_revision_request(BaseModel):
    transcribed_text:str
    client_document: str
    user_document:str

class final_qta_revision_response(BaseModel):
    action_summary:str
    change_details:str
    new_document_text:str
    
class repeat_qta_revision_request(BaseModel):
    transcribed_text: str
    existing_change_details: str
    existing_action_summary: str
    existing_document: str
    