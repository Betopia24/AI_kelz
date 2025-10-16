from fastapi import APIRouter, HTTPException, Form
from app.services.deviation.investigation.investigation import InvestigationService
from app.services.deviation.investigation_new.investigation_new_schema import (
   FirstTimeInvestigationResponse,FirstTimeInvestigationRequest,
)

router = APIRouter()


@router.post("/investigation/first-time-request", tags=["deviation"], response_model=FirstTimeInvestigationResponse)
async def analyze_single_investigation(request: FirstTimeInvestigationRequest):
    """
    Single endpoint for investigation analysis using form-data fields.

    Accepts form fields:
      - incident_1stpart: str (optional)
      - incident_2ndpart: str (optional)
      - incident_full: str (optional)
      - is_attachment: str (optional)

    Returns a structured investigation analysis.
    """
   
    
