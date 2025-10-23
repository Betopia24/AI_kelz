from fastapi import APIRouter, HTTPException
from app.services.deviation.quality_review.quality_review import QualityReviewer
from app.services.deviation.quality_review.quality_review_schema import PerMinuteReview, PerMinuteResponse, FinalQualityReviewRequest, FinalQualityReviewResponse


router = APIRouter()
quality_reviewer = QualityReviewer()

    
@router.post("/per_minute_review", response_model=PerMinuteResponse)
async def get_per_minute_review(request_data: PerMinuteReview):
    try:
        response = quality_reviewer.per_minute_review(request_data)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/final_review", response_model=FinalQualityReviewResponse)
async def get_final_review(request: FinalQualityReviewRequest):

    try:
        response = quality_reviewer.final_review(request)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
