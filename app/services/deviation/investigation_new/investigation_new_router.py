from fastapi import APIRouter, HTTPException, Form
from app.services.deviation.investigation_new.investigation_new import InvestigationService
from app.services.deviation.investigation_new.investigation_new_schema import (
   InvestigationResponse,FirstTimeInvestigationRequest,InvestigationRequest, FinalInvestigationReportResponse,RepeateInvestigationRequest
)

router = APIRouter()
investigation= InvestigationService()

@router.post("/first-time-request", response_model=InvestigationResponse)
async def analyze_single_investigation(request: FirstTimeInvestigationRequest):

    try:
        response = investigation.initial_investigation(request)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/per_minute_investigation", response_model=InvestigationResponse)
async def generate_per_minute_initiation(request_data: InvestigationRequest):
    try:
        response = investigation.per_minute_investigation(request_data)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/final_investigation_report", response_model=FinalInvestigationReportResponse)
async def generate_final_investigation_report(request_data: InvestigationRequest):
    try:
        response = investigation.final_investigation_report(request_data)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/modify_investigation_report", response_model=FinalInvestigationReportResponse)
async def repeat_investigation_report(request_data: RepeateInvestigationRequest):
    try:
        response = investigation.repeat_investigation(request_data)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



    
