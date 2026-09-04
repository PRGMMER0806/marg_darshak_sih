from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.model_schema.user import User
from app.model_schema.attempt import Attempt
from app.model_schema.parent_context import (
    ParentContext,
    ParentContextCreate
)
from app.dependencies import require_role


router = APIRouter(
    prefix="/parent",
    tags=["parent"]
)



async def get_linked_child(
    caller: User,
    student_username: str
):
    """
    Verify that the requested user is:
    1. Actually a student
    2. Linked to this parent
    """

    if not caller.child_ids:
        return None

    if student_username not in caller.child_ids:
        return None

    student = await User.find_one(
        User.username == student_username
    )

    if not student:
        return None

    if student.role != "student":
        return None

    return student




# ---------------------------------------------------------
# PARENT HOME
# ---------------------------------------------------------


@router.get("/home")
async def parent_home(
    current_user: str = Depends(require_role("parent"))
):
    caller = await User.find_one(User.username == current_user)

    if not caller:
        raise HTTPException(status_code=404, detail="Parent not found")

    children = []

    for child_username in caller.child_ids or []:
        child = await User.find_one(User.username == child_username)

        if not child:
            continue

        latest_attempt = await Attempt.find(
            Attempt.user_id == str(child.id),
            Attempt.status == "completed"
        ).sort("-taken_at").first_or_none()

        children.append({
            "student_id": str(child.id),
            "student_username": child.username,
            "latest_score": latest_attempt.score if latest_attempt else None,
            "career_field": (
                latest_attempt.career_field
                if latest_attempt
                else None
            )
        })

    return {
        "role": "parent",
        "message": "Parent home",
        "children": children,
        "endpoints": {
            "child_data": "/parent/child/{student_username}",
            "parent_context": "/parent/context/{student_username}",
            "messages": "/message/inbox",
            "notifications": "/notify/unread-count"
        }
    }




# ---------------------------------------------------------
# CHILD DATA / CHILD DASHBOARD
# ---------------------------------------------------------

@router.get("/child/{student_username}")
async def get_child_data(
    student_username: str,
    current_user: str = Depends(require_role("parent"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Parent not found"
        )

    child = await get_linked_child(
        caller,
        student_username
    )

    if not child:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this student"
        )

    attempts = await Attempt.find(
        Attempt.user_id == str(child.id),
        Attempt.status == "completed"
    ).sort("-taken_at").to_list()

    if not attempts:
        return {
            "student": {
                "id": str(child.id),
                "username": child.username,
                "school_id": child.school_id,
                "class_name": child.class_name
            },
            "progress": {
                "total_attempts": 0,
                "latest_score": None,
                "latest_career_field": None
            },
            "latest_result": None,
            "attempt_history": []
        }

    latest = attempts[0]

    trait_scores = latest.trait_scores or {}

    statistical_evaluation = {
        "aptitude": {
            "numerical": trait_scores.get("apt_numerical"),
            "verbal": trait_scores.get("apt_verbal"),
            "spatial": trait_scores.get("apt_spatial"),
            "logical": trait_scores.get("apt_logical")
        },
        "riasec": {
            "R": trait_scores.get("interest_R"),
            "I": trait_scores.get("interest_I"),
            "A": trait_scores.get("interest_A"),
            "S": trait_scores.get("interest_S"),
            "E": trait_scores.get("interest_E"),
            "C": trait_scores.get("interest_C")
        }
    }

    return {
        "student": {
            "id": str(child.id),
            "username": child.username,
            "school_id": child.school_id,
            "class_name": child.class_name
        },

        "progress": {
            "total_attempts": len(attempts),
            "latest_score": latest.score,
            "latest_career_field": latest.career_field
        },

        "latest_result": {
            "attempt_id": str(latest.id),
            "overall_score": latest.score,

            "top_career": {
                "career_field": latest.career_field,
                "match_score": latest.score
            },

            "persona": latest.persona,

            "statistical_evaluation": statistical_evaluation,

            "top_3_recommendations": (
                latest.recommendations[:3]
                if latest.recommendations
                else []
            ),

            "summary": latest.nlg_summary
        },

        "attempt_history": [
            {
                "attempt_id": str(attempt.id),
                "taken_at": attempt.taken_at,
                "score": attempt.score,
                "career_field": attempt.career_field
            }
            for attempt in attempts
        ]
    }


# ---------------------------------------------------------
# PARENT CONTEXT
# ---------------------------------------------------------

@router.post("/context")
async def submit_context(
    payload: ParentContextCreate,
    current_user: str = Depends(require_role("parent"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Parent not found"
        )

    student = await get_linked_child(
        caller,
        payload.student_id
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to submit context for this student"
        )

    new_context = ParentContext(
        student_id=str(student.id),
        parent_id=str(caller.id),
        note=payload.note,
        submitted_at=datetime.now(timezone.utc)
    )

    await new_context.insert()

    return new_context


# ---------------------------------------------------------
# GET PARENT CONTEXT
# ---------------------------------------------------------

@router.get("/context/{student_username}")
async def get_context(
    student_username: str,
    current_user: str = Depends(require_role("parent"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Parent not found"
        )

    student = await get_linked_child(
        caller,
        student_username
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    contexts = await ParentContext.find(
        ParentContext.student_id == str(student.id),
        ParentContext.parent_id == str(caller.id)
    ).sort("-submitted_at").to_list()

    return {
        "student_username": student.username,
        "contexts": contexts
    }