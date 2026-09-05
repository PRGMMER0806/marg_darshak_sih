from fastapi import APIRouter, Depends, HTTPException
from app.model_schema.attempt import Attempt
from app.dependencies import get_current_user
from app.authorization import check_access

from app.core.career_paths import (
    get_career_path,
    build_match_explanation
)


router = APIRouter(
    tags=["Career path"]
)


@router.get("/career-path/{student_id}")
async def get_career_path_route(
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

    recommendations = latest_attempt.recommendations or []

    career_paths = []

    for recommendation in recommendations[:3]:
        career_field = recommendation.get("career_field")

        if not career_field:
            continue

        match_score = recommendation.get(
            "match_confidence_pct",
            recommendation.get("confidence_pct")
        )

        career_paths.append({
            "rank": recommendation.get("rank"),
            "career_field": career_field,
            "match_score": match_score,
            "why_it_matches": build_match_explanation(
                recommendation
            ),
            "path": get_career_path(career_field),
        })

    return {
        "student_id": str(student.id),
        "attempt_id": str(latest_attempt.id),
        "career_field": latest_attempt.career_field,
        "score": latest_attempt.score,
        "persona": latest_attempt.persona,
        "recommendations": recommendations,
        "summary": latest_attempt.nlg_summary,
        "career_paths": career_paths
    }