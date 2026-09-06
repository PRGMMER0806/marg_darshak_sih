
from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.career_paths import (
    get_career_path,
    build_match_explanation,
)
from app.core.pathway_knowledge import (
    get_pathway_knowledge,
)
from app.core.guidance_decision import (
    analyze_guidance_decision,
)
from app.model_schema.student_interest import (
    StudentInterest,
)
from app.model_schema.education_state import (
    EducationState,
)
from app.model_schema.parent_context import (
    ParentContext,
)
from app.model_schema.teacher_context import (
    TeacherContext,
)


# =========================================================
# ROLE NORMALIZATION
# =========================================================

def _normalize_requester_role(
    requester_role: Any,
) -> Optional[str]:
    """
    Normalize:
        "student"
        "parent"
        "teacher"

    Also supports enum-like values such as:
        UserRole.STUDENT
        UserRole.PARENT
        UserRole.TEACHER
    """

    if requester_role is None:
        return None

    value = getattr(
        requester_role,
        "value",
        requester_role,
    )

    value = str(value).strip().lower()

    if "." in value:
        value = value.rsplit(".", 1)[1]

    if value in {
        "student",
        "parent",
        "teacher",
    }:
        return value

    return value


# =========================================================
# SAFE CONTEXT SERIALIZATION
# =========================================================

def _serialize_parent_context(
    context: Optional[ParentContext],
) -> Optional[Dict[str, Any]]:
    """
    Serialize only the fields required by Guidance.
    """

    if not context:
        return None

    return {
        "student_id": context.student_id,
        "parent_id": context.parent_id,
        "note": context.note,
        "submitted_at": context.submitted_at,
    }


def _serialize_teacher_context(
    context: Optional[TeacherContext],
) -> Optional[Dict[str, Any]]:
    """
    Serialize only the fields required by Guidance.
    """

    if not context:
        return None

    return {
        "student_id": context.student_id,
        "teacher_id": context.teacher_id,
        "academic_grades": (
            context.academic_grades
            if context.academic_grades is not None
            else {}
        ),
        "extracurricular_note": (
            context.extracurricular_note
        ),
        "submitted_at": context.submitted_at,
    }


# =========================================================
# GUIDANCE CONTEXT BUILDER
# =========================================================

async def build_guidance_context(
    student,
    latest_attempt,
    requester_role=None,
    requester_user_id: Optional[str] = None,
):
    """
    Build the structured context provided to the Guidance Agent.

    Authoritative sources:
        - Attempt / assessment
        - Existing ML recommendation
        - Career Path
        - Pathway knowledge

    Guidance-only sources:
        - StudentInterest
        - EducationState
        - ParentContext
        - TeacherContext

    The Guidance Agent NEVER changes the ML result.

    Role behavior:
        student:
            receives student-safe guidance context

        parent:
            receives the parent's own stored context

        teacher:
            receives the teacher's own stored context
    """

    normalized_requester_role = (
        _normalize_requester_role(
            requester_role
        )
    )

    # =====================================================
    # 1. ML / CAREER RECOMMENDATIONS
    # =====================================================

    recommendations = (
        latest_attempt.recommendations
        or []
    )

    top_3 = []

    for recommendation in recommendations[:3]:

        career_field = recommendation.get(
            "career_field"
        )

        if not career_field:
            continue

        match_score = (
            recommendation.get(
                "match_confidence_pct"
            )
            if recommendation.get(
                "match_confidence_pct"
            ) is not None
            else recommendation.get(
                "confidence_pct"
            )
            if recommendation.get(
                "confidence_pct"
            ) is not None
            else recommendation.get(
                "match_score"
            )
        )

        try:
            why_it_matches = (
                build_match_explanation(
                    recommendation
                )
            )
        except Exception:
            why_it_matches = recommendation.get(
                "why_it_matches"
            )

        top_3.append(
            {
                "rank": recommendation.get(
                    "rank"
                ),
                "career_field": career_field,

                # Preserve original recommendation score.
                "match_score": match_score,

                "why_it_matches": (
                    why_it_matches
                ),

                "career_path": (
                    get_career_path(
                        career_field
                    )
                ),

                "pathway_knowledge": (
                    get_pathway_knowledge(
                        career_field
                    )
                ),
            }
        )

    # =====================================================
    # 2. STUDENT INTEREST HISTORY
    # =====================================================

    interest_history = (
        await StudentInterest.find(
            StudentInterest.student_id
            == str(student.id)
        )
        .sort("-stated_at")
        .to_list()
    )

    latest_interest = (
        interest_history[0].interest
        if interest_history
        else None
    )

    interest_history_data = [
        {
            "interest": interest.interest,
            "attempt_id": interest.attempt_id,
            "stated_at": interest.stated_at,
        }
        for interest in interest_history
    ]

    # =========================================================
    # EVOLVING INTEREST SNAPSHOT
    # =========================================================

    current_interest = (
        interest_history[0].interest
        if interest_history
        else None
    )

    previous_interests = [
        item["interest"]
        for item in interest_history_data[1:]
    ]

    evolving_interest_context = {
    "current_interest": current_interest,
    "previous_interests": previous_interests,
    "interest_changed": (
        bool(previous_interests)
        and current_interest is not None
        and current_interest.lower()
        != previous_interests[0].lower()
    ),
}

    # =====================================================
    # 3. STATED INTEREST PATHWAY
    # =====================================================

    stated_interest_pathway = None

    if latest_interest:
        stated_interest_pathway = (
            get_pathway_knowledge(
                latest_interest
            )
        )

    # =====================================================
    # 4. EDUCATION STATE
    # =====================================================

    education_state = (
        await EducationState.find_one(
            EducationState.student_id
            == str(student.id)
        )
    )

    education_state_data = None

    if education_state:

        education_state_data = {
            "school_id": (
                education_state.school_id
            ),
            "class_name": (
                education_state.class_name
            ),
            "academic_grades": (
                education_state.academic_grades
            ),
            "available_streams": (
                education_state.available_streams
            ),
            "eligible_streams": (
                education_state.eligible_streams
            ),
            "preferred_streams": (
                education_state.preferred_streams
            ),
            "allocated_stream": (
                education_state.allocated_stream
            ),
            "updated_by": (
                education_state.updated_by
            ),
            "updated_at": (
                education_state.updated_at
            ),
        }

    # =====================================================
    # 5. ROLE-SPECIFIC HUMAN CONTEXT
    # =====================================================

    parent_context_data = None
    teacher_context_data = None

    # -----------------------------------------------------
    # Parent requester
    # -----------------------------------------------------

    if (
        normalized_requester_role == "parent"
        and requester_user_id
    ):

        parent_context = (
            await ParentContext.find(
                ParentContext.student_id
                == str(student.id),

                ParentContext.parent_id
                == str(requester_user_id),
            )
            .sort("-submitted_at")
            .first_or_none()
        )

        parent_context_data = (
            _serialize_parent_context(
                parent_context
            )
        )

    # -----------------------------------------------------
    # Teacher requester
    # -----------------------------------------------------

    if (
        normalized_requester_role == "teacher"
        and requester_user_id
    ):

        teacher_context = (
            await TeacherContext.find(
                TeacherContext.student_id
                == str(student.id),

                TeacherContext.teacher_id
                == str(requester_user_id),
            )
            .sort("-submitted_at")
            .first_or_none()
        )

        teacher_context_data = (
            _serialize_teacher_context(
                teacher_context
            )
        )

    # =====================================================
    # 6. DETERMINISTIC GUIDANCE DECISION
    # =====================================================

    guidance_decision = (
        analyze_guidance_decision(
            top_3=top_3,
            stated_interest=latest_interest,
            education_state=(
                education_state_data
            ),
        )
    )

    # =====================================================
    # 7. FINAL GUIDANCE CONTEXT
    # =====================================================

    return {

        # -------------------------------------------------
        # Student
        # -------------------------------------------------

        "student": {
            "student_id": str(
                student.id
            ),
            "username": (
                student.username
            ),
            "school_id": (
                student.school_id
            ),
            "class_name": (
                student.class_name
            ),
        },

        # -------------------------------------------------
        # Requester
        # -------------------------------------------------

        "requester": {
            "role": (
                normalized_requester_role
            ),
        },

        # -------------------------------------------------
        # Assessment truth
        # -------------------------------------------------

        "assessment": {
            "attempt_id": str(
                latest_attempt.id
            ),
            "taken_at": (
                latest_attempt.taken_at
            ),
            "submitted_at": (
                latest_attempt.submitted_at
            ),
            "score": (
                latest_attempt.score
            ),
            "trait_scores": (
                latest_attempt.trait_scores
            ),
            "persona": (
                latest_attempt.persona
            ),
            "summary": (
                latest_attempt.nlg_summary
            ),
        },

        # -------------------------------------------------
        # ML truth
        # -------------------------------------------------

        "ml_profile": {
            "career_field": (
                latest_attempt.career_field
            ),

            "top_3": top_3,
        },

        # -------------------------------------------------
        # Guidance-only context
        # -------------------------------------------------

        "guidance_context": {
    "requester_role": normalized_requester_role,
    "student_interest": latest_interest,
    "student_interest_pathway": stated_interest_pathway,
    "interest_history": interest_history_data,
    "evolving_interest_context": evolving_interest_context,
    "teacher_context": teacher_context_data,
    "parent_context": parent_context_data,
    "education_state": education_state_data,
    "decision_analysis": guidance_decision,
},
    }

