from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class PerMinuteReview(BaseModel):
    transcription: str
    quality_review: Optional[str] = None
    sme_review: Optional[str] = None

class PerMinuteResponse(BaseModel):
    quality_review: str
    sme_review: str

class FinalQualityReviewRequest(BaseModel):
    transcription: str
    document: Optional[Dict[str, Any]] = None
    background: str
    immediate_actions: str 
    discussion: str
    root_cause_analysis: List[Dict[str, Any]]
    fishbone_diagram: List[Dict[str, Any]]
    historic_review: str
    capa: str
    impact_assessment: str
    conclusion:str


class FinalQualityReviewResponse(BaseModel):
    background: str
    immediate_actions: str
    discussion: str
    root_cause_analysis: List[Dict[str, Any]]
    fishbone_diagram:List[Dict[str, Any]]
    historical_review: str
    capa: str
    impact_assessment: str
    conclusion: str


class RepeatReviewRequest(BaseModel):
    transcription: str
    background: str
    immediate_actions: str 
    discussion: str
    root_cause_analysis: List[Dict[str, Any]]
    fishbone_diagram: List[Dict[str, Any]]
    historic_review: str
    capa: str
    impact_assessment: str
    conclusion:str
