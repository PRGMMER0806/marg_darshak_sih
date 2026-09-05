from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class EducationState(Document):
    student_id: str

    school_id: Optional[str] = None
    class_name: Optional[str] = None

    academic_grades: Dict[str, float] = Field(
        default_factory=dict
    )

    available_streams: List[str] = Field(
        default_factory=list
    )

    eligible_streams: List[str] = Field(
        default_factory=list
    )

    preferred_streams: List[str] = Field(
        default_factory=list
    )

    allocated_stream: Optional[str] = None

    updated_by: Optional[str] = None
    updated_at: datetime

    class Settings:
        name = "education_states"


class StudentEducationPreferenceRequest(BaseModel):
    preferred_streams: List[str] = Field(
        default_factory=list
    )


class TeacherEducationStateRequest(BaseModel):
    academic_grades: Dict[str, float] = Field(
        default_factory=dict
    )

    available_streams: List[str] = Field(
        default_factory=list
    )

    eligible_streams: List[str] = Field(
        default_factory=list
    )

    allocated_stream: Optional[str] = None