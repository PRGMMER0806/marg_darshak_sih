from fastapi import APIRouter, Depends, HTTPException

from app.model_schema.attempt import Attempt
from app.dependencies import get_current_user
from app.authorization import check_access
from app.core.aggregation import get_weekly_trend, get_peer_average


router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/{student_id}")
async def get_dashboard(
    student_id: str,
    current_user: str = Depends(get_current_user)
):
    # ---------------------------------------------------------
    # VERIFY ACCESS
    # ---------------------------------------------------------

    student = await check_access(current_user, student_id)

    # ---------------------------------------------------------
    # GET COMPLETED ATTEMPTS
    # ---------------------------------------------------------

    attempts = await Attempt.find(
        {
            "user_id": str(student.id),
            "status": "completed"
        }
    ).sort("-taken_at").to_list()

    if not attempts:
        raise HTTPException(
            status_code=404,
            detail="No completed assessment attempts found"
        )

    latest_attempt = attempts[0]

    # ---------------------------------------------------------
    # STATISTICAL EVALUATION
    # ---------------------------------------------------------

    trait_scores = latest_attempt.trait_scores or {}

    statistical_evaluation = {
        "aptitude": {
            "numerical": trait_scores.get("apt_numerical"),
            "verbal": trait_scores.get("apt_verbal"),
            "spatial": trait_scores.get("apt_spatial"),
            "logical": trait_scores.get("apt_logical"),
        },
        "riasec": {
            "R": trait_scores.get("interest_R"),
            "I": trait_scores.get("interest_I"),
            "A": trait_scores.get("interest_A"),
            "S": trait_scores.get("interest_S"),
            "E": trait_scores.get("interest_E"),
            "C": trait_scores.get("interest_C"),
        }
    }

    # ---------------------------------------------------------
    # TOP 3 RECOMMENDATIONS
    # ---------------------------------------------------------

    recommendations = latest_attempt.recommendations or []

    top_3_recommendations = recommendations[:3]

    # ---------------------------------------------------------
    # ATTEMPT HISTORY
    # ---------------------------------------------------------

    attempt_history = [
        {
            "attempt_id": str(attempt.id),
            "taken_at": attempt.taken_at,
            "score": attempt.score,
            "career_field": attempt.career_field,
        }
        for attempt in attempts
    ]

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return {
        "student": {
            "id": str(student.id),
            "username": student.username,
        },

        "progress": {
            "total_attempts": len(attempts),
            "latest_score": latest_attempt.score,
            "latest_career_field": latest_attempt.career_field,
        },

        "latest_result": {
            "attempt_id": str(latest_attempt.id),

            "overall_score": latest_attempt.score,

            "top_career": {
                "career_field": latest_attempt.career_field,
                "match_score": latest_attempt.score,
            },

            "persona": latest_attempt.persona,

            "statistical_evaluation": statistical_evaluation,

            "top_3_recommendations": top_3_recommendations,

            "summary": latest_attempt.nlg_summary,
        },

        "attempt_history": attempt_history,
    }