from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.model_schema.user import User
from app.model_schema.message import Message, MessageCreate
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/message",
    tags=["message"]
)


async def can_message(
    caller: User,
    recipient: User
) -> bool:

    # -----------------------------------------------------
    # Same person
    # -----------------------------------------------------

    if str(caller.id) == str(recipient.id):
        return False

    # -----------------------------------------------------
    # Parent <-> Teacher
    # -----------------------------------------------------

    if {
        caller.role,
        recipient.role
    } == {"parent", "teacher"}:
        return True

    # -----------------------------------------------------
    # Student <-> Parent
    # -----------------------------------------------------

    if caller.role == "student" and recipient.role == "parent":
        return caller.username in (recipient.child_ids or [])

    if caller.role == "parent" and recipient.role == "student":
        return recipient.username in (caller.child_ids or [])

    # -----------------------------------------------------
    # Student <-> Teacher
    # -----------------------------------------------------

    if caller.role == "student" and recipient.role == "teacher":
        return (
            caller.school_id == recipient.school_id
            and caller.class_name == recipient.class_name
        )

    if caller.role == "teacher" and recipient.role == "student":
        return (
            caller.school_id == recipient.school_id
            and caller.class_name == recipient.class_name
        )

    return False


# ---------------------------------------------------------
# SEND MESSAGE
# ---------------------------------------------------------

@router.post("/send")
async def send_message(
    payload: MessageCreate,
    current_user: str = Depends(get_current_user)
):
    caller = await User.find_one(
        User.username == current_user
    )

    if not caller:
        raise HTTPException(
            status_code=404,
            detail="Sender not found"
        )

    recipient = await User.find_one(
        User.username == payload.to_id
    )

    if not recipient:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found"
        )

    if not await can_message(caller, recipient):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to message this user"
        )

    new_message = Message(
        from_id=str(caller.id),
        to_id=str(recipient.id),
        body=payload.body,
        timestamp=datetime.now(timezone.utc)
    )

    await new_message.insert()

    return new_message


# ---------------------------------------------------------
# INBOX
# ---------------------------------------------------------

@router.get("/inbox")
async def get_inbox(
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

    messages = await Message.find(
        Message.to_id == str(caller.id)
    ).sort("-timestamp").to_list()

    return messages