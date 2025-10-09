from pydantic import BaseModel
from typing import Optional,Dict,Any,List


class per_minute_qta_review_request(BaseModel):
    transcribed_text:str
    existing_quality_review:Optional[List[Dict[str,Any]]]=None

class per_minute_qta_review_response(BaseModel):
    quality_review:str
class final_qta_review_request(BaseModel):
    transcribed_text:str
    reference_document: str
    original_document:str

class final_qta_review_response(BaseModel):
    quality_review:List[Dict[str,Any]]
    change_summary:Dict[str, Any] 
    review_summary:str
    new_document_text:str
    