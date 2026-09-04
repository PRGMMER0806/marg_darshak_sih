from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return username

def require_role(required_role: str):
    # returns a dependency function - lets you write Depends(require_role("teacher")) per route
    async def checker(token: str = Depends(oauth2_scheme)):
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if payload.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Not authorized for this role")
        return payload.get("sub")
    return checker