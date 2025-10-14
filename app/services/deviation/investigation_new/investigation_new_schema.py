from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class Discussion(BaseModel):
    discuss_process:str
    equipment:str
    environment:str
    documentation_is_adequate:Literal["Yes", "No"]
    external_communication:str
    personnel_training:str
    equipment_qualification:str

class RootCauseAnalysis(BaseModel):
    brainstorming:str
    five_why:str
    fishbone:str
    five_m:str
    fmea:str

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

class FirstTimeInvestigation(str, Enum):
    existing_background_details:Dict[str, Any]
    existing_impact_assessment: Dict[str, Dict[str, Any]]
    document_information: List[Dict[str, Any]]

class FirstTimeInvestigationResponse(BaseModel):
    background:str
    discussion: Discussion
    root_cause_analysis:RootCauseAnalysis
    final_assessment:FinalAssessment
    historic_review:str
    capa:CAPA