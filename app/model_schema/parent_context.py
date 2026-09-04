from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from datetime import datetime

class ParentContextBase(BaseModel):
    student_id: str  # which student this note is about
    parent_id: str  # who wrote it
    note: str  # behavioral + interest observations



class ParentContextCreate(BaseModel):
    student_id: str  # client only sends this + the note - parent_id/submitted_at set server-side
    note: str

class ParentContext(ParentContextBase, Document):
    submitted_at: datetime  # when it was submitted

    class Settings:
        name = "parent_context"



class ParentContextResponse(ParentContextBase):
    id: PydanticObjectId
    submitted_at: datetime

    class Config:
        json_encoders = {PydanticObjectId: str}