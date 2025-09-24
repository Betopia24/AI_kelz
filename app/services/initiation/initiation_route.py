from fastapi import APIRouter, HTTPException, Body
from app.services.initiation.initiation_schema import PerMinuteInitiationRequest, PerMinuteInitiationResponse
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
