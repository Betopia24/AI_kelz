from fastapi import APIRouter, HTTPException, Body
from app.services.initiation.initiation_schema import (
    PerMinuteInitiationRequest, 
    PerMinuteInitiationResponse,
    FinalCheckRequest,
    FinalRequest,
    FormalIncidentReport
)
from app.services.initiation.initiation import Initiation

router= APIRouter()
summary= Initiation()

@router.post("/per_minute_initiation", response_model=PerMinuteInitiationResponse)
async def generate_per_minute_initiation(request_data: PerMinuteInitiationRequest):
    try:
        response = summary.get_per_minute_summary(request_data)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check_initiation")
async def check_initiation_details(request_data: FinalCheckRequest):
    try:
        response = summary.check_initiation_details(request_data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/generate_incident_report", response_model=FormalIncidentReport)
async def generate_incident_report(request_data: FinalRequest):
    """
    Generate a formal incident report based on transcribed text and any existing details.
    
    The report follows a standardized format with sections for:
    1. Incident title and details
    2. Background information
    3. Meeting attendees
    4. Impact assessment
    5. Criticality determination
    
    Returns a structured incident report according to pharmaceutical quality standards.
    """
    try:
        response = summary.generate_formal_incident_report(request_data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))