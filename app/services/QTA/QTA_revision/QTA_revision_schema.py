from pydantic import BaseModel
from typing import List, Optional,Dict,Any, Union


class per_minute_qta_revision_request(BaseModel):
    transcribed_text:str
    changed_details:Optional[str]=None
    action_summary:Optional[str]=None

class per_minute_qta_revision_response(BaseModel):
    changed_details:str
    action_summary:str
class final_qta_revision_request(BaseModel):
    transcribed_text:str
    documents:Union[List[Dict[str,Any]],str]

class final_qta_revision_response(BaseModel):
    action_summary:str
    change_details:str
    document_text:str
    
class repeat_qta_revision_request(BaseModel):
    transcribed_text: str
    change_details: str
    action_summary: str
    document_text: str
    