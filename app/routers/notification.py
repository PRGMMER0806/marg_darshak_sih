
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import smtplib
import os
from email.message import EmailMessage

from app.model_schema.user import User
from app.model_schema.attempt import Attempt
from app.model_schema.notification import Notification, NotifType
from app.dependencies import get_current_user, require_role


router = APIRouter(prefix="/notify", tags=["notify"])


# =========================================================
# NOTIFICATION CREATION HELPER
# =========================================================

async def create_notification(
    user_id: str,
    notification_type: NotifType,
    message: str
):
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message,
        read=False,
        created_at=datetime.now(timezone.utc)
    )

    await notification.insert()

    return notification


# =========================================================
# EMAIL HELPER
# =========================================================

def send_email(
    to_email: str,
    subject: str,
    body: str
):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Email is optional.
    # Notification is still stored in MongoDB if SMTP
    # configuration is not available.
    if not smtp_email or not smtp_password or not to_email:
        return

    try:
        msg = EmailMessage()

        msg["Subject"] = subject
        msg["From"] = smtp_email
        msg["To"] = to_email

        msg.set_content(body)

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                smtp_email,
                smtp_password
            )

            server.send_message(msg)

    except Exception:
        # Do not allow an email failure to break
        # the application's notification system.
        pass


# =========================================================
# TEACHER — CHECK STUDENTS WHO HAVE NOT APPEARED
# =========================================================

@router.post("/check-inactive")
async def check_inactive(
    current_user: str = Depends(
        require_role("teacher")
    )
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found"
        )

    students = await User.find(
        User.role == "student",
        User.school_id == caller.school_id,
        User.class_name == caller.class_name
    ).to_list()

    notified = []

    for student in students:

        # A student is considered to have appeared
        # only after completing an assessment.
        completed_attempt = await Attempt.find_one(
            Attempt.user_id == str(student.id),
            Attempt.status == "completed"
        )

        if completed_attempt:
            continue

        # Prevent repeated duplicate notifications
        # every time the teacher checks.
        existing_notification = await Notification.find_one(
            Notification.user_id == str(student.id),
            Notification.type == NotifType.missed,
            Notification.read == False
        )

        if existing_notification:
            continue

        message = (
            "You have not completed the aptitude "
            "and career assessment yet."
        )

        await create_notification(
            user_id=str(student.id),
            notification_type=NotifType.missed,
            message=message
        )

        send_email(
            student.email,
            "Assessment Reminder",
            message
        )

        notified.append(student.username)

    return {
        "notified": notified,
        "count": len(notified)
    }


# =========================================================
# GET ALL NOTIFICATIONS
# =========================================================

@router.get("/")
async def get_notifications(
    current_user: str = Depends(get_current_user)
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    notifications = await Notification.find(
        Notification.user_id == str(caller.id)
    ).sort("-created_at").to_list()

    return notifications


# =========================================================
# GET UNREAD COUNT
# =========================================================

@router.get("/unread-count")
async def unread_count(
    current_user: str = Depends(get_current_user)
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    count = await Notification.find(
        Notification.user_id == str(caller.id),
        Notification.read == False
    ).count()

    return {
        "unread_count": count
    }


# =========================================================
# MARK NOTIFICATION AS READ
# =========================================================

@router.post("/{notification_id}/acknowledge")
async def acknowledge(
    notification_id: str,
    current_user: str = Depends(get_current_user)
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    notification = await Notification.get(
        notification_id
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    # A user can only acknowledge their own notification.
    if notification.user_id != str(caller.id):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to modify this notification"
        )

    notification.read = True

    await notification.save()

    return notification

