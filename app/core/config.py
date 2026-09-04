import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(
    dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env"
)

SECRET_KEY = os.getenv("SECRET_KEY")  # used to sign JWTs
ALGORITHM = "HS256"  # HMAC signing algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token validity window

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")  # fail loudly at startup, not silently later