from beanie import Document
from datetime import datetime
from enum import Enum

class NotifType(str, Enum):
    missed = "missed"
    attended = "attended"
    score_update = "score_update"
    followup = "followup"
    endorsement = "endorsement"

class Notification(Document):
    user_id: str
    type: NotifType
    message: str
    read: bool = False
    created_at: datetime

    class Settings:
        name = "notifications"