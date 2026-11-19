from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import JWT_HOURS, JWT_SECRET
from .db import User, get_db

bearer = HTTPBearer(auto_error=False)


def hash_pw(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def check_pw(p: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(p.encode(), h.encode())
    except Exception:
        return False


def make_token(uid: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_HOURS)
    return jwt.encode({"sub": str(uid), "exp": exp}, JWT_SECRET, algorithm="HS256")


def optional_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(get_db)):
    if not cred:
        return None
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=["HS256"])
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(401, "Session expired or invalid token. Please log in again.")
    return db.get(User, uid)


def require_user(user=Depends(optional_user)):
    if not user:
        raise HTTPException(401, "Please log in to use this feature.")
    return user
