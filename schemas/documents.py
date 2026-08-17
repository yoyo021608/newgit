from pydantic import BaseModel
from datetime import datetime

class DocumentCreate(BaseModel):
    filename: str
    file_path: str
    file_type: str
    user_id: int

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True