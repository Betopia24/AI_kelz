from pydantic import BaseModel
from typing import Optional,Dict,Any,List


class per_minute_qta_review_request(BaseModel):
    transcribed_text:str
    quality_review:Optional[List[Dict[str,Any]]]=None
    change_summary:Optional[str]=None
    review_summary: Optional[str]=None


class per_minute_qta_review_response(BaseModel):
    quality_review:List[Dict[str,Any]]
    change_summary:str
    review_summary:str
class final_qta_review_request(BaseModel):
    transcribed_text:str
    reference_document: Optional[str]
    original_document:str

class final_qta_review_response(BaseModel):
    quality_review:List[Dict[str,Any]]
    change_summary:str
    review_summary:str
    document_text:str

class repeat_qta_review_request(BaseModel):
    transcribed_text: str
    document: str
    quality_review: List[Dict[str,Any]]
    change_summary: str
    review_summary: str
    