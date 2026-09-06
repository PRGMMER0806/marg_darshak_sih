from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import Field


class GuidanceConversationMessage(Document):
    student_id: str
    requester_id: str
    requester_role: Literal["student", "parent", "teacher"]

    attempt_id: str | None = None

    role: Literal["user", "assistant"]
    content: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "guidance_conversations"
        indexes = [
            [
                ("student_id", 1),
                ("requester_id", 1),
                ("requester_role", 1),
                ("created_at", -1),
            ]
        ]