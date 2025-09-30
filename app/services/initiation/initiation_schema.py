from pydantic import BaseModel
from typing import Literal, Optional, List, Dict, Any


class ImpactAssessmentItem(BaseModel):
    impact: Literal["Yes", "No"]
    severity: Literal["Low", "Medium", "High", ""]


class ImpactAssessment(BaseModel):
    Product_Quality: ImpactAssessmentItem
    Patient_Safety: ImpactAssessmentItem
    Regulatory_Impact: ImpactAssessmentItem
    Validation_Impact: ImpactAssessmentItem


class BackgroundDetails(BaseModel):
    Who: str
    What: str
    Where: str
    Immediate_Action: str
    Quality_Concerns: str
    Quality_Controls: str
    RCA_tool: str
    Expected_Interim_Action: str
    CAPA: str

class PerMinuteInitiationRequest(BaseModel):
    transcribed_text: str
    existing_incident_title: Optional[str] = None
    existing_background_details: Optional[Dict[str, Any]] = None
    existing_background_attendee: Optional[List[str]] = None
    existing_impact_assessment: Optional[Dict[str, Dict[str, Any]]] = None


class PerMinuteInitiationResponse(BaseModel):
    incident_title: str
    background_details: BackgroundDetails
    background_attendee: List[str]  
    impact_assessment: ImpactAssessment

class FinalCheckRequest(BaseModel):
    existing_background_details: Dict[str, Any]
