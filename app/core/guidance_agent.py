from app.core.career_paths import (
    get_career_path,
    build_match_explanation,
)

from app.core.pathway_knowledge import get_pathway_knowledge
from app.model_schema.student_interest import StudentInterest
from app.model_schema.education_state import EducationState
from app.core.guidance_decision import analyze_guidance_decision

async def build_guidance_context(student, latest_attempt):
    """
    Build the structured context that will eventually be
    provided to the Guidance Agent.

    Assessment/ML data is authoritative.
    Student interest is stored separately as guidance context.
    """

    recommendations = latest_attempt.recommendations or []
    top_3 = []

    for recommendation in recommendations[:3]:
        career_field = recommendation.get("career_field")

        if not career_field:
            continue

        top_3.append({
    "rank": recommendation.get("rank"),
    "career_field": career_field,
    "match_score": recommendation.get(
        "match_confidence_pct",
        recommendation.get("confidence_pct")
    ),
    "why_it_matches": build_match_explanation(
        recommendation
    ),
    "career_path": get_career_path(
        career_field
    ),
    "pathway_knowledge": get_pathway_knowledge(
        career_field
    ),
})

    # -----------------------------------------------------
    # Student interest history
    # -----------------------------------------------------
    interest_history = await StudentInterest.find(
        StudentInterest.student_id == str(student.id)
    ).sort("-stated_at").to_list()

    # Latest stated interest
    latest_interest = (
        interest_history[0].interest
        if interest_history
        else None
    )

    # Clean response data
    interest_history_data = [
        {
            "interest": interest.interest,
            "attempt_id": interest.attempt_id,
            "stated_at": interest.stated_at,
        }
        for interest in interest_history
    ]


    stated_interest_pathway = get_pathway_knowledge(
    latest_interest
)


    education_state = await EducationState.find_one(
    EducationState.student_id == str(student.id)
)

    education_state_data = None

    if education_state:
        education_state_data = {
            "school_id": education_state.school_id,
            "class_name": education_state.class_name,
            "academic_grades": education_state.academic_grades,
            "available_streams": education_state.available_streams,
            "eligible_streams": education_state.eligible_streams,
            "preferred_streams": education_state.preferred_streams,
            "allocated_stream": education_state.allocated_stream,
            "updated_by": education_state.updated_by,
            "updated_at": education_state.updated_at,
        }

    guidance_decision = analyze_guidance_decision(
    top_3=top_3,
    stated_interest=latest_interest,
    education_state=education_state_data,
)

    # -----------------------------------------------------
    # Final guidance context
    # -----------------------------------------------------
    return {
        "student": {
            "student_id": str(student.id),
            "username": student.username,
            "school_id": student.school_id,
            "class_name": student.class_name,
        },

        "assessment": {
            "attempt_id": str(latest_attempt.id),
            "taken_at": latest_attempt.taken_at,
            "submitted_at": latest_attempt.submitted_at,
            "score": latest_attempt.score,
            "trait_scores": latest_attempt.trait_scores,
            "persona": latest_attempt.persona,
            "summary": latest_attempt.nlg_summary,
        },

        "ml_profile": {
            "career_field": latest_attempt.career_field,
            "top_3": top_3,
        },

        "guidance_context": {
    "student_interest": latest_interest,
    "student_interest_pathway": stated_interest_pathway,
    "interest_history": interest_history_data,
    "teacher_context": None,
    "parent_context": None,
    "education_state": education_state_data,
    "decision_analysis": guidance_decision,
},
    }