from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field

from app.model_schema.question import (
    AptitudeQuestion,
    RiasecQuestion
)
from app.model_schema.attempt import Attempt
from app.model_schema.answer import Answer
from app.model_schema.user import User

from app.dependencies import get_current_user
from app.core.scoring import (
    calculate_trait_scores,
    predict_career
)


router = APIRouter(
    prefix="/aptitude",
    tags=["aptitude"]
)


# =========================================================
# CONSTANTS
# =========================================================

ASSESSMENT_DURATION_MINUTES = 1

ASSESSMENT_DURATION_SECONDS = (
    ASSESSMENT_DURATION_MINUTES * 60
)

FREEZE_LIMIT_MINUTES = 30

FREEZE_LIMIT_SECONDS = (
    FREEZE_LIMIT_MINUTES * 60
)


# =========================================================
# REQUEST SCHEMAS
# =========================================================

class SubmitPayload(BaseModel):

    aptitude_answers: dict[str, int] = Field(
        default_factory=dict
    )

    riasec_answers: dict[str, int] = Field(
        default_factory=dict
    )


# =========================================================
# HELPER
# =========================================================

def utc_now() -> datetime:
    """
    Always return timezone-aware UTC datetime.
    """
    return datetime.utcnow()


# =========================================================
# CREATE FRESH ATTEMPT
# =========================================================

async def create_fresh_attempt(user_doc: User):

    started_at = utc_now()

    expires_at = (
        started_at
        + timedelta(
            seconds=ASSESSMENT_DURATION_SECONDS
        )
    )

    attempt = Attempt(
        user_id=str(user_doc.id),
        taken_at=started_at,
        started_at=started_at,
        expires_at=expires_at,
        remaining_seconds=ASSESSMENT_DURATION_SECONDS,
        paused_at=None,
        status="in_progress",
    )

    await attempt.insert()

    return attempt


# =========================================================
# RESET ATTEMPT
# =========================================================

async def reset_attempt(attempt: Attempt):

    # Remove all answers belonging to the old attempt.
    await Answer.find(
        Answer.attempt_id == str(attempt.id)
    ).delete()

    # Remove the old attempt completely.
    await attempt.delete()

@router.post("/{attempt_id}/timeout")
async def timeout_assessment(
    attempt_id: str,
    current_user: str = Depends(get_current_user)
):
    user_doc = await User.find_one(
        User.username == current_user
    )

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    attempt = await Attempt.get(attempt_id)

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Assessment attempt not found"
        )

    # Ownership check
    if attempt.user_id != str(user_doc.id):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to reset this assessment"
        )

    # Never reset a completed assessment
    if attempt.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Completed assessment cannot be reset"
        )

    # Timeout applies only to an actively running assessment
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=400,
            detail="Assessment is not currently running"
        )

    # Server-side expiration check
    now = utc_now()

    if attempt.expires_at is not None and now < attempt.expires_at:
        raise HTTPException(
            status_code=400,
            detail="Assessment has not expired yet"
        )

    # Delete attempt + all associated answers
    await reset_attempt(attempt)

    return {
        "message": "Assessment timed out and was reset successfully",
        "reset": True
    }


# =========================================================
# START ASSESSMENT
# =========================================================

@router.post("/start")
async def start_assessment(
    current_user: str = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Find current user
    # -----------------------------------------------------

    user_doc = await User.find_one(
        User.username == current_user
    )

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Check for an existing active attempt
    # -----------------------------------------------------

    existing_attempt = await Attempt.find_one(
        Attempt.user_id == str(user_doc.id),
        Attempt.status == "in_progress"
    )

    if existing_attempt:

        now = utc_now()

        # -------------------------------------------------
        # Check whether active timer has expired
        # -------------------------------------------------

        if (
            existing_attempt.expires_at is None
            or now >= existing_attempt.expires_at
        ):

            existing_attempt.status = "expired"

            existing_attempt.remaining_seconds = 0

            await existing_attempt.save()

        else:

            # Calculate the actual remaining time.
            remaining = int(
                (
                    existing_attempt.expires_at - now
                ).total_seconds()
            )

            remaining = max(0, remaining)

            existing_attempt.remaining_seconds = remaining

            await existing_attempt.save()

            return {
                "message": "An assessment is already in progress",
                "attempt_id": str(existing_attempt.id),
                "started_at": existing_attempt.started_at,
                "expires_at": existing_attempt.expires_at,
                "remaining_seconds": remaining,
                "status": existing_attempt.status,
            }

    # -----------------------------------------------------
    # Check for a paused attempt
    # -----------------------------------------------------

    paused_attempt = await Attempt.find_one(
        Attempt.user_id == str(user_doc.id),
        Attempt.status == "paused"
    )

    if paused_attempt:

        now = utc_now()

        if paused_attempt.paused_at:

            frozen_seconds = int(
                (
                    now - paused_attempt.paused_at
                ).total_seconds()
            )

            # ---------------------------------------------
            # Freeze period exceeded 30 minutes
            # ---------------------------------------------

            if frozen_seconds > FREEZE_LIMIT_SECONDS:

                await reset_attempt(paused_attempt)

                # Start completely fresh assessment.
                attempt = await create_fresh_attempt(
                    user_doc
                )

                return {
                    "message": (
                        "Previous assessment was reset "
                        "because the freeze period exceeded "
                        "30 minutes"
                    ),
                    "attempt_id": str(attempt.id),
                    "started_at": attempt.started_at,
                    "expires_at": attempt.expires_at,
                    "remaining_seconds": (
                        attempt.remaining_seconds
                    ),
                    "duration_minutes": (
                        ASSESSMENT_DURATION_MINUTES
                    ),
                    "status": attempt.status,
                    "reset": True,
                }

            # ---------------------------------------------
            # Still inside freeze window
            # ---------------------------------------------

            return {
                "message": (
                    "Assessment is paused. "
                    "Resume the existing attempt."
                ),
                "attempt_id": str(paused_attempt.id),
                "started_at": paused_attempt.started_at,
                "expires_at": None,
                "remaining_seconds": (
                    paused_attempt.remaining_seconds
                ),
                "paused_at": paused_attempt.paused_at,
                "freeze_remaining_seconds": (
                    FREEZE_LIMIT_SECONDS
                    - frozen_seconds
                ),
                "status": paused_attempt.status,
                "reset": False,
            }

    # -----------------------------------------------------
    # No active/paused attempt
    # -----------------------------------------------------

    attempt = await create_fresh_attempt(user_doc)

    return {
        "message": "Assessment started",
        "attempt_id": str(attempt.id),
        "started_at": attempt.started_at,
        "expires_at": attempt.expires_at,
        "remaining_seconds": attempt.remaining_seconds,
        "duration_minutes": ASSESSMENT_DURATION_MINUTES,
        "status": attempt.status,
        "reset": False,
    }


# =========================================================
# PAUSE ASSESSMENT
# =========================================================

@router.post("/{attempt_id}/pause")
async def pause_assessment(
    attempt_id: str,
    current_user: str = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    user_doc = await User.find_one(
        User.username == current_user
    )

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Find attempt
    # -----------------------------------------------------

    attempt = await Attempt.get(attempt_id)

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Assessment attempt not found"
        )

    # -----------------------------------------------------
    # Ownership
    # -----------------------------------------------------

    if attempt.user_id != str(user_doc.id):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to pause this assessment"
        )

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    if attempt.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Completed assessment cannot be paused"
        )

    if attempt.status == "expired":
        raise HTTPException(
            status_code=400,
            detail="Expired assessment cannot be paused"
        )

    if attempt.status == "paused":
        return {
            "message": "Assessment is already paused",
            "attempt_id": str(attempt.id),
            "remaining_seconds": attempt.remaining_seconds,
            "paused_at": attempt.paused_at,
            "status": attempt.status,
        }

    # -----------------------------------------------------
    # Server-side timer calculation
    # -----------------------------------------------------

    now = utc_now()

    if attempt.expires_at is None:
        raise HTTPException(
            status_code=400,
            detail="Assessment timer is invalid"
        )

    remaining = int(
        (
            attempt.expires_at - now
        ).total_seconds()
    )

    remaining = max(0, remaining)

    # -----------------------------------------------------
    # Timer already expired
    # -----------------------------------------------------

    if remaining <= 0:

        attempt.remaining_seconds = 0
        attempt.status = "expired"
        attempt.expires_at = None

        await attempt.save()

        raise HTTPException(
            status_code=400,
            detail="Assessment time has expired"
        )

    # -----------------------------------------------------
    # Freeze the timer
    # -----------------------------------------------------

    attempt.remaining_seconds = remaining

    attempt.paused_at = now

    attempt.expires_at = None

    attempt.status = "paused"

    await attempt.save()

    return {
        "message": "Assessment paused successfully",
        "attempt_id": str(attempt.id),
        "remaining_seconds": attempt.remaining_seconds,
        "paused_at": attempt.paused_at,
        "freeze_limit_minutes": FREEZE_LIMIT_MINUTES,
        "freeze_limit_seconds": FREEZE_LIMIT_SECONDS,
        "status": attempt.status,
    }


# =========================================================
# RESUME ASSESSMENT
# =========================================================

@router.post("/{attempt_id}/resume")
async def resume_assessment(
    attempt_id: str,
    current_user: str = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    user_doc = await User.find_one(
        User.username == current_user
    )

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Find attempt
    # -----------------------------------------------------

    attempt = await Attempt.get(attempt_id)

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Assessment attempt not found"
        )

    # -----------------------------------------------------
    # Ownership
    # -----------------------------------------------------

    if attempt.user_id != str(user_doc.id):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to resume this assessment"
        )

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    if attempt.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="This assessment has already been completed"
        )

    if attempt.status == "expired":
        raise HTTPException(
            status_code=400,
            detail="This assessment has expired"
        )

    if attempt.status != "paused":
        raise HTTPException(
            status_code=400,
            detail="This assessment is not paused"
        )

    # -----------------------------------------------------
    # Validate paused_at
    # -----------------------------------------------------

    if attempt.paused_at is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid paused assessment"
        )

    now = utc_now()

    frozen_seconds = int(
        (
            now - attempt.paused_at
        ).total_seconds()
    )

    # -----------------------------------------------------
    # Freeze period exceeded
    # -----------------------------------------------------

    if frozen_seconds > FREEZE_LIMIT_SECONDS:

        await reset_attempt(attempt)

        # Completely fresh attempt.
        new_attempt = await create_fresh_attempt(
            user_doc
        )

        return {
            "message": (
                "Previous assessment was reset "
                "because it remained paused for more "
                "than 30 minutes"
            ),
            "attempt_id": str(new_attempt.id),
            "started_at": new_attempt.started_at,
            "expires_at": new_attempt.expires_at,
            "remaining_seconds": (
                new_attempt.remaining_seconds
            ),
            "duration_minutes": (
                ASSESSMENT_DURATION_MINUTES
            ),
            "status": new_attempt.status,
            "reset": True,
        }

    # -----------------------------------------------------
    # Make sure remaining active time exists
    # -----------------------------------------------------

    if attempt.remaining_seconds <= 0:

        await reset_attempt(attempt)

        new_attempt = await create_fresh_attempt(
            user_doc
        )

        return {
            "message": (
                "Previous assessment had no time remaining. "
                "A new assessment has been started."
            ),
            "attempt_id": str(new_attempt.id),
            "started_at": new_attempt.started_at,
            "expires_at": new_attempt.expires_at,
            "remaining_seconds": (
                new_attempt.remaining_seconds
            ),
            "duration_minutes": (
                ASSESSMENT_DURATION_MINUTES
            ),
            "status": new_attempt.status,
            "reset": True,
        }

    # -----------------------------------------------------
    # Resume timer
    # -----------------------------------------------------

    attempt.expires_at = (
        now
        + timedelta(
            seconds=attempt.remaining_seconds
        )
    )

    attempt.paused_at = None

    attempt.status = "in_progress"

    await attempt.save()

    return {
        "message": "Assessment resumed successfully",
        "attempt_id": str(attempt.id),
        "expires_at": attempt.expires_at,
        "remaining_seconds": attempt.remaining_seconds,
        "status": attempt.status,
        "reset": False,
    }


# =========================================================
# GET QUESTIONS
# =========================================================

@router.get("/questions")
async def get_questions(
    current_user: str = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Authentication check
    # -----------------------------------------------------

    user_doc = await User.find_one(
        User.username == current_user
    )

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Get questions
    # -----------------------------------------------------

    aptitude_questions = (
        await AptitudeQuestion.find_all().to_list()
    )

    riasec_questions = (
        await RiasecQuestion.find_all().to_list()
    )

    # -----------------------------------------------------
    # Remove correct answers
    # -----------------------------------------------------

    safe_aptitude_questions = []

    for q in aptitude_questions:

        safe_aptitude_questions.append({
            "id": q.id_code,
            "category": q.category,
            "type": q.type,
            "difficulty": q.difficulty,
            "prompt": q.prompt,
            "options": q.options,
        })

    safe_riasec_questions = []

    for q in riasec_questions:

        safe_riasec_questions.append({
            "id": q.id_code,
            "category": q.category,
            "type": q.type,
            "statement": q.statement,
            "scale": q.scale,
        })

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "aptitude_questions": safe_aptitude_questions,
        "riasec_questions": safe_riasec_questions,
        "total_questions": (
            len(safe_aptitude_questions)
            + len(safe_riasec_questions)
        ),
        "duration_minutes": ASSESSMENT_DURATION_MINUTES,
        "duration_seconds": ASSESSMENT_DURATION_SECONDS,
        "freeze_limit_minutes": FREEZE_LIMIT_MINUTES,
        "freeze_limit_seconds": FREEZE_LIMIT_SECONDS,
    }


# =========================================================
# SUBMIT ASSESSMENT
# =========================================================

@router.post("/{attempt_id}/submit")
async def submit_attempt(
    attempt_id: str,
    payload: SubmitPayload,
    current_user: str = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Find current user
    # -----------------------------------------------------

    user_doc = await User.find_one(
        User.username == current_user
    )

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Find attempt
    # -----------------------------------------------------

    attempt = await Attempt.get(attempt_id)

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Assessment attempt not found"
        )

    # -----------------------------------------------------
    # Ownership check
    # -----------------------------------------------------

    if attempt.user_id != str(user_doc.id):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to submit this assessment"
        )

    # -----------------------------------------------------
    # Status check
    # -----------------------------------------------------

    if attempt.status == "completed":

        raise HTTPException(
            status_code=400,
            detail="This assessment has already been submitted"
        )

    if attempt.status == "expired":

        raise HTTPException(
            status_code=400,
            detail="This assessment has expired"
        )

    if attempt.status == "paused":

        raise HTTPException(
            status_code=400,
            detail=(
                "Assessment is currently paused. "
                "Resume it before submitting."
            )
        )

    if attempt.status != "in_progress":

        raise HTTPException(
            status_code=400,
            detail="Assessment is not active"
        )

    # -----------------------------------------------------
    # Server-side time check
    # -----------------------------------------------------

    now = utc_now()

    if attempt.expires_at is None:

        raise HTTPException(
            status_code=400,
            detail="Assessment timer is invalid"
        )

    remaining = int(
        (
            attempt.expires_at - now
        ).total_seconds()
    )

    # -----------------------------------------------------
    # Assessment expired
    # -----------------------------------------------------

    if remaining <= 0:

        attempt.remaining_seconds = 0
        attempt.status = "expired"
        attempt.expires_at = None

        await attempt.save()

        raise HTTPException(
            status_code=400,
            detail="Assessment time has expired"
        )

    # -----------------------------------------------------
    # Keep remaining time updated
    # -----------------------------------------------------

    attempt.remaining_seconds = remaining

    # -----------------------------------------------------
    # Load questions
    # -----------------------------------------------------

    aptitude_questions = (
        await AptitudeQuestion.find_all().to_list()
    )

    riasec_questions = (
        await RiasecQuestion.find_all().to_list()
    )

    # -----------------------------------------------------
    # Expected question IDs
    # -----------------------------------------------------

    expected_aptitude_ids = {
        q.id_code
        for q in aptitude_questions
    }

    expected_riasec_ids = {
        q.id_code
        for q in riasec_questions
    }

    # -----------------------------------------------------
    # Received IDs
    # -----------------------------------------------------

    received_aptitude_ids = set(
        payload.aptitude_answers.keys()
    )

    received_riasec_ids = set(
        payload.riasec_answers.keys()
    )

    # -----------------------------------------------------
    # Missing answers
    # -----------------------------------------------------

    missing_aptitude = (
        expected_aptitude_ids
        - received_aptitude_ids
    )

    missing_riasec = (
        expected_riasec_ids
        - received_riasec_ids
    )

    # -----------------------------------------------------
    # Unknown answers
    # -----------------------------------------------------

    unknown_aptitude = (
        received_aptitude_ids
        - expected_aptitude_ids
    )

    unknown_riasec = (
        received_riasec_ids
        - expected_riasec_ids
    )

    # -----------------------------------------------------
    # Validate missing
    # -----------------------------------------------------

    if missing_aptitude or missing_riasec:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "All questions must be answered",
                "missing_aptitude": sorted(
                    missing_aptitude
                ),
                "missing_riasec": sorted(
                    missing_riasec
                ),
            }
        )

    # -----------------------------------------------------
    # Validate unknown
    # -----------------------------------------------------

    if unknown_aptitude or unknown_riasec:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unknown question IDs submitted",
                "unknown_aptitude": sorted(
                    unknown_aptitude
                ),
                "unknown_riasec": sorted(
                    unknown_riasec
                ),
            }
        )

    # -----------------------------------------------------
    # Validate aptitude answers
    # -----------------------------------------------------

    for question in aptitude_questions:

        answer = payload.aptitude_answers[
            question.id_code
        ]

        if not isinstance(answer, int):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid answer for "
                    f"{question.id_code}"
                )
            )

        if (
            answer < 0
            or answer >= len(question.options)
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid option index for "
                    f"{question.id_code}"
                )
            )

    # -----------------------------------------------------
    # Validate RIASEC answers
    # -----------------------------------------------------

    for question in riasec_questions:

        answer = payload.riasec_answers[
            question.id_code
        ]

        if not isinstance(answer, int):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid answer for "
                    f"{question.id_code}"
                )
            )

        if answer < 1 or answer > 5:

            raise HTTPException(
                status_code=400,
                detail=(
                    "RIASEC answer must be between "
                    f"1 and 5 for {question.id_code}"
                )
            )

    # -----------------------------------------------------
    # Remove old answers
    # -----------------------------------------------------

    await Answer.find(
        Answer.attempt_id == str(attempt.id)
    ).delete()

    # -----------------------------------------------------
    # Save answers
    # -----------------------------------------------------

    answer_documents = []

    # -----------------------------------------------------
    # Aptitude answers
    # -----------------------------------------------------

    for (
        question_id,
        answer_value
    ) in payload.aptitude_answers.items():

        answer_documents.append(
            Answer(
                attempt_id=str(attempt.id),
                question_id=question_id,
                question_type="aptitude",
                answer_value=answer_value,
            )
        )

    # -----------------------------------------------------
    # RIASEC answers
    # -----------------------------------------------------

    for (
        question_id,
        answer_value
    ) in payload.riasec_answers.items():

        answer_documents.append(
            Answer(
                attempt_id=str(attempt.id),
                question_id=question_id,
                question_type="riasec",
                answer_value=answer_value,
            )
        )

    if answer_documents:

        await Answer.insert_many(
            answer_documents
        )

    # -----------------------------------------------------
    # Calculate ML features
    # -----------------------------------------------------

    trait_scores = await calculate_trait_scores(
        payload.aptitude_answers,
        payload.riasec_answers
    )

    # -----------------------------------------------------
    # ML prediction
    # -----------------------------------------------------

    result = predict_career(trait_scores)

    # -----------------------------------------------------
    # Complete attempt
    # -----------------------------------------------------

    attempt.submitted_at = now

    attempt.status = "completed"

    attempt.expires_at = None

    attempt.remaining_seconds = remaining

    attempt.paused_at = None

    attempt.trait_scores = trait_scores

    attempt.career_field = result["career_field"]

    attempt.score = result["score"]

    attempt.persona = result["persona"]

    attempt.recommendations = (
        result["recommendations"]
    )

    attempt.nlg_summary = (
        result["nlg_summary"]
    )

    await attempt.save()

    # -----------------------------------------------------
    # Final response
    # -----------------------------------------------------

    return {
        "message": "Assessment submitted successfully",
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "submitted_at": attempt.submitted_at,
        "result": {
            "career_field": attempt.career_field,
            "score": attempt.score,
            "persona": attempt.persona,
            "recommendations": (
                attempt.recommendations
            ),
            "summary": attempt.nlg_summary,
            "trait_scores": attempt.trait_scores,
        },
    }

