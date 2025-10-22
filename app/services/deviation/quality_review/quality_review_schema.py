from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime


class PerMinuteReview(BaseModel):
    transcription: str
    existing_quality_review: Optional[str] = None
    existing_sme_review: Optional[str] = None

class PerMinuteResponse(BaseModel):
    quality_review: str
    sme_review: str

class FinalQualityReview(BaseModel):
    transcription: str
    document: Optional[str] = None
    existing_background: str
    existing_discussion: List[Dict[str, Any]]  
    existing_root_cause_analysis: List[Dict[str, Any]]
    existing_final_assessment: List[Dict[str, Any]]  
    existing_historic_review: List[Dict[str, Any]] 
    existing_capa: List[Dict[str, Any]] 
    existing_attendees:Optional[List[str]]=None


class FinalQualityReviewResponse(BaseModel):
    transcription: str
    document:str
    background: str
    immediate_actions: str
    discussion: str
    root_cause_analysis: List[Dict[str, Any]]
    fishbone_diagram:List[Dict[str, Any]]
    historical_review: str
    capa: str
    impact_assessment: str
    conclusion: str
