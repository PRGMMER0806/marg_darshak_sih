from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_role
from app.model_schema.user import User


router = APIRouter(
    prefix="/student",
    tags=["student"]
)


@router.get("/home")
async def student_home(
    current_user: str = Depends(require_role("student"))
):
    student = await User.find_one(
        User.username == current_user
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "username": student.username,
        "role": "student",
        "message": "Student home",
        "endpoints": {
            "assessment": "/aptitude/start",
            "dashboard": f"/dashboard/{student.id}",
            "career_path": f"/career-path/{student.id}",
            "messages": "/message/inbox",
            "notifications": "/notify/unread-count"
        }
    }