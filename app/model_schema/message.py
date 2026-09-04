from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    from_id: str  # sender's real _id
    to_id: str  # recipient's real _id
    body: str  # message content

class MessageCreate(BaseModel):
    to_id: str  # client sends this as a username - resolved to real _id server-side
    body: str


class Message(MessageBase, Document):
    timestamp: datetime

    class Settings:
        name = "messages"



class MessageResponse(MessageBase):
    id: PydanticObjectId
    timestamp: datetime

    class Config:
        json_encoders = {PydanticObjectId: str}