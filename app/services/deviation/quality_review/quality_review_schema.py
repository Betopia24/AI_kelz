from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class PerMinuteReview(BaseModel):
    transcription: str
    existing_quality_review: Optional[str] = None
    existing_sme_review: Optional[str] = None

class PerMinuteResponse(BaseModel):
    quality_review: str
    sme_review: str

class FinalQualityReviewRequest(BaseModel):
    transcription: str
    document: Optional[Dict[str, Any]] = None
    existing_background: str
    existing_immediate_actions: str 
    existing_discussion: str
    existing_root_cause_analysis: List[Dict[str, Any]]
    existing_fishbone_diagram: List[Dict[str, Any]]
    existing_historic_review: str
    existing_capa: str
    existing_impact_assessment: str
    existing_conclusion:str


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
