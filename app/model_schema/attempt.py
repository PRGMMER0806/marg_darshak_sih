from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


# =========================================================
# ATTEMPT STATUS
# =========================================================

AttemptStatus = Literal[
    "in_progress",
    "paused",
    "completed",
    "expired"
]


# =========================================================
# BASE MODEL
# =========================================================

class AttemptBase(BaseModel):
    user_id: str
    taken_at: datetime


# =========================================================
# ATTEMPT DOCUMENT
# =========================================================

class Attempt(AttemptBase, Document):

    # -----------------------------------------------------
    # Timer fields
    # -----------------------------------------------------

    started_at: datetime

    # When assessment is active:
    #   expires_at = current time + remaining active time
    #
    # When assessment is paused:
    #   expires_at = None
    expires_at: Optional[datetime] = None

    # Stores how much ACTIVE assessment time remains.
    #
    # Maximum value = 5400 seconds (90 minutes)
    remaining_seconds: int = 5400

    # Time at which the assessment was paused.
    #
    # Used to enforce the 30-minute freeze window.
    paused_at: Optional[datetime] = None

    # -----------------------------------------------------
    # Assessment state
    # -----------------------------------------------------

    submitted_at: Optional[datetime] = None

    status: AttemptStatus = "in_progress"

    # -----------------------------------------------------
    # Assessment result
    # -----------------------------------------------------

    score: Optional[float] = None

    career_field: Optional[str] = None

    trait_scores: Optional[dict] = None

    persona: Optional[dict] = None

    recommendations: Optional[list] = None

    nlg_summary: Optional[str] = None

    # -----------------------------------------------------
    # MongoDB collection
    # -----------------------------------------------------

    class Settings:
        name = "attempts"


# =========================================================
# RESPONSE MODEL
# =========================================================

class AttemptResponse(AttemptBase):

    id: PydanticObjectId

    started_at: datetime

    expires_at: Optional[datetime] = None

    remaining_seconds: int = 5400

    paused_at: Optional[datetime] = None

    submitted_at: Optional[datetime] = None

    status: AttemptStatus

    score: Optional[float] = None

    career_field: Optional[str] = None

    trait_scores: Optional[dict] = None

    persona: Optional[dict] = None

    recommendations: Optional[list] = None

    nlg_summary: Optional[str] = None

    class Config:
        json_encoders = {
            PydanticObjectId: str
        }