from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.model_schema.user import User
from app.model_schema.attempt import Attempt
from app.model_schema.notification import Notification,NotifType
from app.model_schema.teacher_context import (
    TeacherContext,
    TeacherContextCreate
)
from app.model_schema.flag import (
    FollowUpFlag,
    Endorsement
)
from app.dependencies import require_role


router = APIRouter(
    prefix="/teacher",
    tags=["teacher"]
)


# ---------------------------------------------------------
# CLASS STUDENTS
# ---------------------------------------------------------

async def get_class_students(caller: User):
    """
    Return students belonging to the teacher's
    school + class.
    """

    return await User.find(
        User.role == "student",
        User.school_id == caller.school_id,
        User.class_name == caller.class_name
    ).to_list()


async def get_teacher_student(
    caller: User,
    student_username: str
):
    """
    Return a student only if:
    - the user exists
    - the user is actually a student
    - the student belongs to the teacher's school
    - the student belongs to the teacher's class
    """

    student = await User.find_one(
        User.username == student_username
    )

    if not student:
        return None

    if student.role != "student":
        return None

    if student.school_id != caller.school_id:
        return None

    if student.class_name != caller.class_name:
        return None

    return student




# ---------------------------------------------------------
# TEACHER HOME
# ---------------------------------------------------------


@router.get("/home")
async def teacher_home(
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(User.username == current_user)

    if not caller:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "username": caller.username,
        "role": "teacher",
        "school_id": caller.school_id,
        "class_name": caller.class_name,
        "message": "Teacher home",
        "endpoints": {
            "dashboard": "/teacher/dashboard",
            "individual_student": "/teacher/student/{student_username}",
            "not_appeared": "/teacher/not-appeared",
            "messages": "/message/inbox",
            "notifications": "/notify/unread-count"
        }
    }



# ---------------------------------------------------------
# COLLECTIVE CLASS DASHBOARD
# ---------------------------------------------------------

@router.get("/dashboard")
async def teacher_dashboard(
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    students = await get_class_students(caller)

    student_data = []

    completed_count = 0

    for student in students:

        latest_attempt = await Attempt.find(
            Attempt.user_id == str(student.id),
            Attempt.status == "completed"
        ).sort("-taken_at").first_or_none()

        if latest_attempt:
            completed_count += 1

        student_data.append({
            "student_id": str(student.id),
            "student_username": student.username,
            "latest_score": (
                latest_attempt.score
                if latest_attempt
                else None
            ),
            "career_field": (
                latest_attempt.career_field
                if latest_attempt
                else None
            ),
            "has_completed_assessment": (
                latest_attempt is not None
            )
        })

    return {
        "class_name": caller.class_name,
        "school_id": caller.school_id,

        "statistics": {
            "total_students": len(students),
            "completed_assessment": completed_count,
            "not_appeared": len(students) - completed_count
        },

        "students": student_data
    }


# ---------------------------------------------------------
# INDIVIDUAL STUDENT DATA
# ---------------------------------------------------------

@router.get("/student/{student_username}")
async def teacher_student_data(
    student_username: str,
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    student = await get_teacher_student(
        caller,
        student_username
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this student"
        )

    attempts = await Attempt.find(
        Attempt.user_id == str(student.id),
        Attempt.status == "completed"
    ).sort("-taken_at").to_list()

    if not attempts:
        return {
            "student": {
                "id": str(student.id),
                "username": student.username,
                "school_id": student.school_id,
                "class_name": student.class_name
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
            "id": str(student.id),
            "username": student.username,
            "school_id": student.school_id,
            "class_name": student.class_name
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
# NOT APPEARED
# ---------------------------------------------------------

@router.get("/not-appeared")
async def not_appeared(
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    students = await get_class_students(caller)

    missing = []

    for student in students:

        completed_attempt = await Attempt.find_one(
            Attempt.user_id == str(student.id),
            Attempt.status == "completed"
        )

        if not completed_attempt:
            missing.append({
                "student_id": str(student.id),
                "student_username": student.username
            })

    return {
        "class_name": caller.class_name,
        "not_appeared": missing
    }


# ---------------------------------------------------------
# TEACHER CONTEXT
# ---------------------------------------------------------

@router.post("/context")
async def submit_context(
    payload: TeacherContextCreate,
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    student = await get_teacher_student(
        caller,
        payload.student_id
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to submit context for this student"
        )

    new_context = TeacherContext(
        student_id=str(student.id),
        teacher_id=str(caller.id),
        academic_grades=payload.academic_grades,
        extracurricular_note=payload.extracurricular_note,
        submitted_at=datetime.now(timezone.utc)
    )

    await new_context.insert()

    return new_context


# ---------------------------------------------------------
# GET TEACHER CONTEXT
# ---------------------------------------------------------

@router.get("/context/{student_username}")
async def get_teacher_context(
    student_username: str,
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    student = await get_teacher_student(
        caller,
        student_username
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    contexts = await TeacherContext.find(
        TeacherContext.student_id == str(student.id),
        TeacherContext.teacher_id == str(caller.id)
    ).sort("-submitted_at").to_list()

    return {
        "student_username": student.username,
        "contexts": contexts
    }


# ---------------------------------------------------------
# FLAG STUDENT FOR FOLLOW-UP
# ---------------------------------------------------------

@router.post("/flag-followup/{student_username}")
async def flag_followup(
    student_username: str,
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(User.username == current_user)

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    student = await get_teacher_student(
        caller,
        student_username
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    # Save the teacher's follow-up flag
    flag = FollowUpFlag(
        student_id=str(student.id),
        teacher_id=str(caller.id),
        created_at=datetime.now(timezone.utc)
    )

    await flag.insert()

    # Notify the student
    notification = Notification(
        user_id=str(student.id),
        type=NotifType.followup,
        message=(
            "Your teacher has flagged your career progress "
            "for follow-up."
        ),
        read=False,
        created_at=datetime.now(timezone.utc)
    )

    await notification.insert()

    return {
        "flag": flag,
        "notification": notification
    }

# ---------------------------------------------------------
# ENDORSE CAREER PATH
# ---------------------------------------------------------

@router.post("/endorse-path/{student_username}")
async def endorse_path(
    student_username: str,
    current_user: str = Depends(require_role("teacher"))
):
    caller = await User.find_one(User.username == current_user)

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    student = await get_teacher_student(
        caller,
        student_username
    )

    if not student:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    # Save the teacher's endorsement
    endorsement = Endorsement(
        student_id=str(student.id),
        teacher_id=str(caller.id),
        endorsed=True,
        created_at=datetime.now(timezone.utc)
    )

    await endorsement.insert()

    # Notify the student
    notification = Notification(
        user_id=str(student.id),
        type=NotifType.endorsement,
        message=(
            "Your teacher has endorsed your current "
            "career direction."
        ),
        read=False,
        created_at=datetime.now(timezone.utc)
    )

    await notification.insert()

    return {
        "endorsement": endorsement,
        "notification": notification
    }