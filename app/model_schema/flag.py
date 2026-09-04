from beanie import Document
from datetime import datetime

class FollowUpFlag(Document):
    student_id: str
    teacher_id: str
    created_at: datetime

    class Settings:
        name = "followup_flags"

class Endorsement(Document):
    student_id: str
    teacher_id: str
    endorsed: bool
    created_at: datetime

    class Settings:
        name = "endorsements"