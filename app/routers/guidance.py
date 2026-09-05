from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.dependencies import get_current_user
from app.authorization import check_access
from app.model_schema.attempt import Attempt
from app.model_schema.user import User, UserRole
from app.model_schema.student_interest import (
    StudentInterest,
    StudentInterestRequest,
)
from app.model_schema.education_state import (
    EducationState,
    StudentEducationPreferenceRequest,
    TeacherEducationStateRequest,
)
from app.core.guidance_agent import build_guidance_context


router = APIRouter(
    prefix="/guidance",
    tags=["Guidance"]
)


@router.get("/{student_id}/context")
async def get_guidance_context(
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

    return await build_guidance_context(
    student,
    latest_attempt
)


@router.post("/{student_id}/interest")
async def add_student_interest(
    student_id: str,
    payload: StudentInterestRequest,
    current_user: str = Depends(get_current_user)
):
    # -----------------------------------------------------
    # Verify logged-in user
    # -----------------------------------------------------
    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if not current_user_doc:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Only the student themselves can submit an interest
    # -----------------------------------------------------
    if current_user_doc.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=403,
            detail="Only the student can submit their own interest"
        )

    # -----------------------------------------------------
    # Verify student exists and matches logged-in user
    # -----------------------------------------------------
    student = await User.find_one(
        User.username == student_id
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    if student.id != current_user_doc.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to submit interest for this student"
        )

    # -----------------------------------------------------
    # Validate interest
    # -----------------------------------------------------
    interest = payload.interest.strip()

    if not interest:
        raise HTTPException(
            status_code=400,
            detail="Interest cannot be empty"
        )

    # -----------------------------------------------------
    # Find the latest completed assessment
    # -----------------------------------------------------
    latest_attempt = await Attempt.find(
        Attempt.user_id == str(student.id),
        Attempt.status == "completed"
    ).sort("-submitted_at").first_or_none()

    # -----------------------------------------------------
    # Store interest as a new historical record
    # -----------------------------------------------------
    interest_record = StudentInterest(
        student_id=str(student.id),
        interest=interest,
        attempt_id=(
            str(latest_attempt.id)
            if latest_attempt
            else None
        ),
        stated_at=datetime.utcnow()
    )

    await interest_record.insert()

    return {
        "message": "Student interest recorded successfully",
        "interest": interest_record.interest,
        "attempt_id": interest_record.attempt_id,
        "stated_at": interest_record.stated_at,
    }


@router.post("/{student_id}/education-preferences")
async def update_student_education_preferences(
    student_id: str,
    payload: StudentEducationPreferenceRequest,
    current_user: str = Depends(get_current_user)
):
    student = await check_access(
        current_user,
        student_id
    )

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if current_user_doc.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=403,
            detail="Only the student can update their stream preferences"
        )

    if current_user_doc.id != student.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update this student's preferences"
        )

    preferences = [
        stream.strip()
        for stream in payload.preferred_streams
        if stream.strip()
    ]

    education_state = await EducationState.find_one(
        EducationState.student_id == str(student.id)
    )

    if education_state:
        education_state.preferred_streams = preferences
        education_state.updated_by = current_user
        education_state.updated_at = datetime.utcnow()

        await education_state.save()
    else:
        education_state = EducationState(
            student_id=str(student.id),
            school_id=student.school_id,
            class_name=student.class_name,
            preferred_streams=preferences,
            updated_by=current_user,
            updated_at=datetime.utcnow(),
        )

        await education_state.insert()

    return {
        "message": "Education preferences updated successfully",
        "student_id": str(student.id),
        "preferred_streams": education_state.preferred_streams,
    }



@router.post("/{student_id}/education-state")
async def update_teacher_education_state(
    student_id: str,
    payload: TeacherEducationStateRequest,
    current_user: str = Depends(get_current_user)
):
    student = await check_access(
        current_user,
        student_id
    )

    current_user_doc = await User.find_one(
        User.username == current_user
    )

    if current_user_doc.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403,
            detail="Only the teacher can update the official education state"
        )

    education_state = await EducationState.find_one(
        EducationState.student_id == str(student.id)
    )

    if education_state:
        education_state.academic_grades = payload.academic_grades
        education_state.available_streams = payload.available_streams
        education_state.eligible_streams = payload.eligible_streams
        education_state.allocated_stream = payload.allocated_stream
        education_state.school_id = student.school_id
        education_state.class_name = student.class_name
        education_state.updated_by = current_user
        education_state.updated_at = datetime.utcnow()

        await education_state.save()
    else:
        education_state = EducationState(
            student_id=str(student.id),
            school_id=student.school_id,
            class_name=student.class_name,
            academic_grades=payload.academic_grades,
            available_streams=payload.available_streams,
            eligible_streams=payload.eligible_streams,
            allocated_stream=payload.allocated_stream,
            updated_by=current_user,
            updated_at=datetime.utcnow(),
        )

        await education_state.insert()

    return {
        "message": "Education state updated successfully",
        "student_id": str(student.id),
        "education_state": {
            "academic_grades": education_state.academic_grades,
            "available_streams": education_state.available_streams,
            "eligible_streams": education_state.eligible_streams,
            "preferred_streams": education_state.preferred_streams,
            "allocated_stream": education_state.allocated_stream,
            "updated_by": education_state.updated_by,
            "updated_at": education_state.updated_at,
        },
    }