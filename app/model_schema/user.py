from beanie import Document, PydanticObjectId
from pydantic import BaseModel,EmailStr
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"

#a common model that the req model, table and resp model inherits for respective tasks
#this contains all required details except private ones
class UserBase(BaseModel):
    
    username: str
    email: EmailStr
    mobile: str
    role: UserRole
    school_id: str | None = None  # used with class_name to uniquely identify a class (students & teachers)
    class_name: str | None = None  # e.g. "10-A" - only unique when paired with school_id
    child_ids: list[str] | None = None  # parent only - list of linked students' User._id (as strings)

#req model
class UserReq(UserBase):

    #gets all private details, if none just pass
    password : str


#table model
class User(UserBase, Document):

    hashed_password : str
    #inherits base, so automatically gets all details, in case private one(password) store its hashed version here
    class Settings:
        name = "users"


#resp model
class UserRes(UserBase):

    id: PydanticObjectId  # matches Beanie's actual auto-generated id type

    class Config:
        json_encoders = {PydanticObjectId: str}  # ensures clean string output in JSON