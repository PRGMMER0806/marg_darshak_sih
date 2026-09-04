from fastapi import HTTPException
from beanie import PydanticObjectId

from app.model_schema.user import User


async def check_access(
    current_user: str,
    student_id: str
) -> User:

    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    try:
        student_object_id = PydanticObjectId(student_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid student ID"
        )

    student = await User.get(student_object_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    if student.role != "student":
        raise HTTPException(
            status_code=400,
            detail="Target user is not a student"
        )

    is_self = (
        caller.role == "student"
        and caller.id == student.id
    )

    is_parent = (
        caller.role == "parent"
        and student.username in (caller.child_ids or [])
    )

    is_teacher = (
        caller.role == "teacher"
        and caller.school_id == student.school_id
        and caller.class_name == student.class_name
    )

    if not (is_self or is_parent or is_teacher):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this student's data"
        )

    return student