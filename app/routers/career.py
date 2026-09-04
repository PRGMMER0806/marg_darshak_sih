from fastapi import APIRouter, Depends, HTTPException

from app.model_schema.attempt import Attempt
from app.dependencies import get_current_user
from app.authorization import check_access


router = APIRouter(
    tags=["Career path"]
)


@router.get("/career-path/{student_id}")
async def get_career_path(
    student_id: str,
    current_user: str = Depends(get_current_user)
):

    student = await check_access(
        current_user,
        student_id
    )

    latest_attempt = await Attempt.find(
        Attempt.user_id == str(student.id),
        Attempt.status == "completed"
    ).sort("-submitted_at").first_or_none()

    if not latest_attempt:

        raise HTTPException(
            status_code=404,
            detail="No completed assessment found for this student"
        )

    return {
        "student_id": str(student.id),

        "attempt_id": str(latest_attempt.id),

        "career_field": latest_attempt.career_field,

        "score": latest_attempt.score,

        "persona": latest_attempt.persona,

        "recommendations": latest_attempt.recommendations,

        "summary": latest_attempt.nlg_summary
    }