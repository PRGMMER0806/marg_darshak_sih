from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from datetime import datetime

class TeacherContextBase(BaseModel):
    student_id: str
    teacher_id: str
    academic_grades: dict[str, float] | None = None  # subject: grade (converted to a standard 0-100 scale, per your earlier note)
    extracurricular_note: str | None = None  # freeform - achievements, activities, leadership



class TeacherContextCreate(BaseModel):
    student_id: str
    academic_grades: dict[str, float] | None = None
    extracurricular_note: str | None = None




class TeacherContext(TeacherContextBase, Document):
    submitted_at: datetime

    class Settings:
        name = "teacher_context"




class TeacherContextResponse(TeacherContextBase):
    id: PydanticObjectId
    submitted_at: datetime

    class Config:
        json_encoders = {PydanticObjectId: str}