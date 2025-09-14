from pydantic import BaseModel, Field
from typing import Any, Dict

class InvestigationModifyInput(BaseModel):
    investigation_response: Dict[str, Any] = Field(..., description="Original response from investigation endpoint to be modified.")
    # Note: The audio file will be uploaded separately in the route as UploadFile, not through this schema.

# In your endpoint, use:
# - 'investigation_response' from this model (parsed from JSON body)
# - 'instruction_audio' as UploadFile (from multipart/form-data)
