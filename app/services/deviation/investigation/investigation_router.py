from fastapi import APIRouter, HTTPException, Form
from app.services.deviation.investigation.investigation import InvestigationService
from app.services.deviation.investigation.investigation_schema import (
    SingleInvestigationResponse,
)

router = APIRouter()


@router.post("/investigation/analyze", tags=["deviation"], response_model=SingleInvestigationResponse)
async def analyze_single_investigation(
    incident_1stpart: str = Form(None, description="First part of the incident description"),
    incident_2ndpart: str = Form(None, description="Second part of the incident description"),
    incident_full: str = Form(None, description="Full incident description"),
    is_attachment: str = Form(None, description="Whether there is an attachment")
):
    """
    Single endpoint for investigation analysis using form-data fields.

    Accepts form fields:
      - incident_1stpart: str (optional)
      - incident_2ndpart: str (optional)
      - incident_full: str (optional)
      - is_attachment: str (optional)

    Returns a structured investigation analysis.
    """
    # Validate required text fields (optional, so only warn if all are missing)
    if not any([incident_1stpart, incident_2ndpart, incident_full]):
        raise HTTPException(status_code=400, detail="At least one incident field must be provided.")

    result = InvestigationService.analyze_simple_input(
        incident_description=incident_1stpart or "",
        background_information=incident_2ndpart or "",
        initial_observations=incident_full or "",
    )

    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Investigation analysis failed: {result.get('error', 'Unknown error')}",
        )

    return SingleInvestigationResponse(
        status="success",
        investigation_analysis=result,
        message="Investigation analysis completed successfully",
    )
