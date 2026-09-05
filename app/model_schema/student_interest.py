from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class StudentInterest(Document):
    student_id: str
    interest: str

    # Assessment context when the interest was expressed
    attempt_id: Optional[str] = None

    # When the student expressed this interest
    stated_at: datetime

    class Settings:
        name = "student_interests"


class StudentInterestRequest(BaseModel):
    interest: str