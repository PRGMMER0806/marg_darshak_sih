from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.model_schema.user import User, UserReq, UserRes
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    home: str
    user_id: str


@router.post("/register", response_model=UserRes)
async def register(user_in: UserReq):
    existing_username = await User.find_one(
        User.username == user_in.username
    )

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    existing_email = await User.find_one(
        User.email == user_in.email
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        **user_in.model_dump(exclude={"password"}),
        hashed_password=hash_password(user_in.password),
    )

    await new_user.insert()

    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await User.find_one(
        User.username == credentials.username
    )

    if not user or not verify_password(
        credentials.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    role = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )

    token = create_access_token(
        data={
            "sub": user.username,
            "role": role,
        }
    )

    home_routes = {
        "student": "/student/home",
        "parent": "/parent/home",
        "teacher": "/teacher/home",
    }

    home = home_routes.get(role)

    if home is None:
        raise HTTPException(
            status_code=500,
            detail="Invalid user role configured"
        )

    return Token(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=role,
        home=home,
        user_id=str(user.id),
    )