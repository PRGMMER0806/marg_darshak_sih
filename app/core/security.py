from datetime import datetime, timedelta, timezone
import jwt  # PyJWT - handles tokens
from jwt import PyJWTError
from passlib.context import CryptContext  # passlib - handles password hashing
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")  # argon2 hashing

def hash_password(password: str) -> str:
    return pwd_context.hash(password)  # one-way hash, never store plain text

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)  # compares plain vs hash

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()  # don't mutate caller's dict
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})  # "exp" claim makes the token expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # sign and return token string

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # verifies signature + expiry
    except PyJWTError:
        return None  # invalid or expired token