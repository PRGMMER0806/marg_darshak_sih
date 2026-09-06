
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel

from app.dependencies import (
    get_current_user,
)

from app.authorization import (
    check_access,
)

from app.model_schema.attempt import (
    Attempt,
)

from app.model_schema.user import (
    User,
    UserRole,
)

from app.model_schema.student_interest import (
    StudentInterest,
    StudentInterestRequest,
)

from app.model_schema.education_state import (
    EducationState,
    StudentEducationPreferenceRequest,
    TeacherEducationStateRequest,
)

from app.core.guidance_agent import (
    build_guidance_context,
)

from app.core.guidance_llm import (
    generate_guidance,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/guidance",
    tags=["Guidance"],
)


# =========================================================
# REQUEST SCHEMA
# =========================================================

class GuidanceGenerationRequest(BaseModel):
    question: Optional[str] = None


# =========================================================
# GET GUIDANCE CONTEXT
# =========================================================

@router.get("/{student_id}/context")
async def get_guidance_context(
    student_id: str,
    current_user: str = Depends(
        get_current_user
    ),
):

    # =====================================================
    # 1. AUTHORIZATION
    # =====================================================

    student = await check_access(
        current_user,
        student_id,
    )

    # =====================================================
    # 2. IDENTIFY REQUESTER
    # =====================================================

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if not current_user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # =====================================================
    # 3. FIND LATEST COMPLETED ASSESSMENT
    # =====================================================

    latest_attempt = await Attempt.find(
        Attempt.user_id == str(
            student.id
        ),
        Attempt.status == "completed",
    ).sort(
        "-submitted_at"
    ).first_or_none()

    if not latest_attempt:
        raise HTTPException(
            status_code=404,
            detail=(
                "No completed assessment found "
                "for this student"
            ),
        )

    # =====================================================
    # 4. BUILD GUIDANCE CONTEXT
    # =====================================================

    guidance_context = (
        await build_guidance_context(
            student=student,
            latest_attempt=latest_attempt,
            requester_role=(
                current_user_doc.role
            ),
            requester_user_id=str(
                current_user_doc.id
            ),
        )
    )

    return guidance_context


# =========================================================
# ADD STUDENT INTEREST
# =========================================================

@router.post("/{student_id}/interest")
async def add_student_interest(
    student_id: str,
    payload: StudentInterestRequest,
    current_user: str = Depends(
        get_current_user
    ),
):

    # =====================================================
    # 1. VERIFY LOGGED-IN USER
    # =====================================================

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if not current_user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # =====================================================
    # 2. STUDENT ONLY
    # =====================================================

    if current_user_doc.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the student can submit "
                "their own interest"
            ),
        )

    # =====================================================
    # 3. RESOLVE STUDENT
    # =====================================================

    student = await User.find_one(
        User.username == student_id
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    # =====================================================
    # 4. VERIFY OWN STUDENT
    # =====================================================

    if student.id != current_user_doc.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not allowed to submit "
                "interest for this student"
            ),
        )

    # =====================================================
    # 5. VALIDATE INTEREST
    # =====================================================

    interest = payload.interest.strip()

    if not interest:
        raise HTTPException(
            status_code=400,
            detail="Interest cannot be empty",
        )

    # =====================================================
    # 6. FIND LATEST COMPLETED ASSESSMENT
    # =====================================================

    latest_attempt = await Attempt.find(
        Attempt.user_id == str(
            student.id
        ),
        Attempt.status == "completed",
    ).sort(
        "-submitted_at"
    ).first_or_none()

    # =====================================================
    # 7. CREATE NEW HISTORICAL INTEREST RECORD
    # =====================================================

    interest_record = StudentInterest(
        student_id=str(
            student.id
        ),
        interest=interest,
        attempt_id=(
            str(latest_attempt.id)
            if latest_attempt
            else None
        ),
        stated_at=datetime.utcnow(),
    )

    await interest_record.insert()

    return {
        "message": (
            "Student interest recorded successfully"
        ),
        "interest": (
            interest_record.interest
        ),
        "attempt_id": (
            interest_record.attempt_id
        ),
        "stated_at": (
            interest_record.stated_at
        ),
    }


# =========================================================
# STUDENT EDUCATION PREFERENCES
# =========================================================

@router.post(
    "/{student_id}/education-preferences"
)
async def update_student_education_preferences(
    student_id: str,
    payload: StudentEducationPreferenceRequest,
    current_user: str = Depends(
        get_current_user
    ),
):

    # =====================================================
    # 1. AUTHORIZATION
    # =====================================================

    student = await check_access(
        current_user,
        student_id,
    )

    # =====================================================
    # 2. VERIFY CURRENT USER
    # =====================================================

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if not current_user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # =====================================================
    # 3. STUDENT ONLY
    # =====================================================

    if current_user_doc.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the student can update "
                "their stream preferences"
            ),
        )

    if current_user_doc.id != student.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not allowed to update "
                "this student's preferences"
            ),
        )

    # =====================================================
    # 4. CLEAN PREFERENCES
    # =====================================================

    preferences = [
        stream.strip()
        for stream in payload.preferred_streams
        if stream.strip()
    ]

    # =====================================================
    # 5. FIND EXISTING STATE
    # =====================================================

    education_state = (
        await EducationState.find_one(
            EducationState.student_id
            == str(student.id)
        )
    )

    # =====================================================
    # 6. UPDATE OR CREATE
    # =====================================================

    if education_state:

        education_state.preferred_streams = (
            preferences
        )

        education_state.updated_by = (
            current_user
        )

        education_state.updated_at = (
            datetime.utcnow()
        )

        await education_state.save()

    else:

        education_state = EducationState(
            student_id=str(
                student.id
            ),

            school_id=(
                student.school_id
            ),

            class_name=(
                student.class_name
            ),

            preferred_streams=(
                preferences
            ),

            updated_by=current_user,

            updated_at=datetime.utcnow(),
        )

        await education_state.insert()

    return {
        "message": (
            "Education preferences updated successfully"
        ),
        "student_id": str(
            student.id
        ),
        "preferred_streams": (
            education_state.preferred_streams
        ),
    }


# =========================================================
# TEACHER EDUCATION STATE
# =========================================================

@router.post(
    "/{student_id}/education-state"
)
async def update_teacher_education_state(
    student_id: str,
    payload: TeacherEducationStateRequest,
    current_user: str = Depends(
        get_current_user
    ),
):

    # =====================================================
    # 1. AUTHORIZATION
    # =====================================================

    student = await check_access(
        current_user,
        student_id,
    )

    # =====================================================
    # 2. VERIFY CURRENT USER
    # =====================================================

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if not current_user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # =====================================================
    # 3. TEACHER ONLY
    # =====================================================

    if current_user_doc.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the teacher can update "
                "the official education state"
            ),
        )

    # =====================================================
    # 4. FIND EXISTING STATE
    # =====================================================

    education_state = (
        await EducationState.find_one(
            EducationState.student_id
            == str(student.id)
        )
    )

    # =====================================================
    # 5. UPDATE OR CREATE
    # =====================================================

    if education_state:

        education_state.academic_grades = (
            payload.academic_grades
        )

        education_state.available_streams = (
            payload.available_streams
        )

        education_state.eligible_streams = (
            payload.eligible_streams
        )

        education_state.allocated_stream = (
            payload.allocated_stream
        )

        education_state.school_id = (
            student.school_id
        )

        education_state.class_name = (
            student.class_name
        )

        education_state.updated_by = (
            current_user
        )

        education_state.updated_at = (
            datetime.utcnow()
        )

        await education_state.save()

    else:

        education_state = EducationState(
            student_id=str(
                student.id
            ),

            school_id=(
                student.school_id
            ),

            class_name=(
                student.class_name
            ),

            academic_grades=(
                payload.academic_grades
            ),

            available_streams=(
                payload.available_streams
            ),

            eligible_streams=(
                payload.eligible_streams
            ),

            allocated_stream=(
                payload.allocated_stream
            ),

            updated_by=current_user,

            updated_at=datetime.utcnow(),
        )

        await education_state.insert()

    return {
        "message": (
            "Education state updated successfully"
        ),

        "student_id": str(
            student.id
        ),

        "education_state": {

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
        },
    }


# =========================================================
# GENERATE GUIDANCE
# =========================================================

@router.post(
    "/{student_id}/generate"
)
async def generate_student_guidance(
    student_id: str,
    payload: GuidanceGenerationRequest,
    current_user: str = Depends(
        get_current_user
    ),
):

    # =====================================================
    # 1. AUTHORIZATION
    # =====================================================

    student = await check_access(
        current_user,
        student_id,
    )

    # =====================================================
    # 2. IDENTIFY REQUESTER
    # =====================================================

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if not current_user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # =====================================================
    # 3. FIND LATEST COMPLETED ASSESSMENT
    # =====================================================

    latest_attempt = await Attempt.find(
        Attempt.user_id == str(
            student.id
        ),
        Attempt.status == "completed",
    ).sort(
        "-submitted_at"
    ).first_or_none()

    if not latest_attempt:
        raise HTTPException(
            status_code=404,
            detail=(
                "No completed assessment found "
                "for this student"
            ),
        )

    # =====================================================
    # 4. BUILD AUTHORITATIVE CONTEXT
    # =====================================================

    guidance_context = (
        await build_guidance_context(
            student=student,

            latest_attempt=latest_attempt,

            requester_role=(
                current_user_doc.role
            ),

            requester_user_id=str(
                current_user_doc.id
            ),
        )
    )

    # =====================================================
    # 5. CALL GUIDANCE AGENT
    # =====================================================

    try:

        guidance = await generate_guidance(
            guidance_context=(
                guidance_context
            ),

            user_question=(
                payload.question
            ),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    # =====================================================
    # 6. RETURN RESULT
    # =====================================================

    requester_role = getattr(
        current_user_doc.role,
        "value",
        current_user_doc.role,
    )

    return {

        "student_id": str(
            student.id
        ),

        "attempt_id": str(
            latest_attempt.id
        ),

        "requester_role": str(
            requester_role
        ),

        "guidance": guidance,
    }

