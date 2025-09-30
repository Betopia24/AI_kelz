from pydantic import BaseModel
from typing import List

class AttachementRequest(BaseModel):
    user_input:str
    exsting_file_titles:List [str]

class AttachementResponse (BaseModel):
    new_file_titles:List[str]