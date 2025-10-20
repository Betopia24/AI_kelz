from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
class Discussion(BaseModel):
    discuss_process:str
    equipment:str
    environment:str
    documentation_is_adequate:Literal["Yes", "No"]
    external_communication:str
    personnel_training:str
    equipment_qualification:str

class FishboneAnalysis(BaseModel):
    Machine:str
    Material:str
    fishbone:str
    five_m:str
    fmea:str
class RootCauseAnalysis(BaseModel):
    FishboneAnalysis:FishboneAnalysis
    FiveWhy:str

class FinalAssessment(BaseModel):
    patient_safety:str
    product_quality:str
    compliance_impact:str
    validation_impact:str
    regulatory_impact:str

class CAPA(BaseModel):
    correction:str
    interim_action:str
    corrective_action:str
    preventive_action:str

class FirstTimeInvestigationRequest(BaseModel):
    existing_background_details:Dict[str, Any]
    existing_impact_assessment: Dict[str, Dict[str, Any]]
    document_information: List[Dict[str, Any]]

class InvestigationRequest(BaseModel):
    transcript: str
    existing_background:Optional[str]=None
    existing_discussion: Optional[Discussion]=None
    existing_root_cause_analysis:Optional[RootCauseAnalysis]=None
    existing_final_assessment:Optional[FinalAssessment]=None
    existing_historic_review:Optional[str]=None
    existing_capa:Optional[CAPA]=None
    exisiting_attendees:Optional[List[str]]=None

class InvestigationResponse(BaseModel):
    background:str
    discussion: Discussion
    root_cause_analysis:RootCauseAnalysis
    final_assessment:FinalAssessment
    historic_review:str
    capa:CAPA

class FinalInvestigationReportResponse(BaseModel):
    background: str
    immediate_actions: str
    discussion: str
    root_cause_analysis: RootCauseAnalysis
    fishbone_diagram:List[Dict[str, Any]]
    historical_review: str
    capa: str
    impact_assessment: str
    conclusion: str