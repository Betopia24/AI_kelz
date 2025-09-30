from fastapi import APIRouter, HTTPException, Body
from app.services.deviation.attachement_new.attachement_new_schema import AttachementRequest, AttachementResponse
from app.services.deviation.attachement_new.attachement_new import AttachementTitle

router= APIRouter()
attachement= AttachementTitle()


@router.post("/change_attachment_titles")
async def check_initiation_details(request_data: AttachementRequest):
    try:
        response = attachement.change_file_titles(request_data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))