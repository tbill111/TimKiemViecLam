from __future__ import annotations

import datetime as dt
from typing import Optional

import bcrypt
import jwt

from .config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt(rounds=get_settings().bcrypt_rounds)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("ascii"))
    except ValueError:
        return False


def create_token(user_id: int, role: str) -> str:
    s = get_settings()
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=s.jwt_expire_hours)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_token(token: str) -> Optional[int]:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
