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
    incident_title: Optional[str] = None
    background_details: Optional[Dict[str, Any]] = None
    background_attendee: Optional[List[str]] = None
    impact_assessment: Optional[Dict[str, Dict[str, Any]]] = None
    criticality: Optional[str] = None


class PerMinuteInitiationResponse(BaseModel):
    incident_title: str
    background_details: BackgroundDetails
    background_attendee: List[str]  
    impact_assessment: ImpactAssessment
    criticality: str

class FinalCheckRequest(BaseModel):
    background_details: Dict[str, Any]

class FinalRequest(BaseModel):
    transcribed_text: str
    incident_title: Optional[str] = None
    background_details: Optional[Dict[str, Any]] = None
    background_attendee: Optional[List[str]] = None
    impact_assessment: Optional[Dict[str, Dict[str, Any]]] = None

class IncidentReportSection(BaseModel):
    content: str

class FormalIncidentReport(BaseModel):
    incident_title: IncidentReportSection
    background: IncidentReportSection
    meeting_attendees: IncidentReportSection
    impact_assessment: IncidentReportSection
    criticality: IncidentReportSection

class ModifyIncidentReportRequest(BaseModel):
    report: FormalIncidentReport
    modifications: str
