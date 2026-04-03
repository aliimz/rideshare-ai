"""
Password hashing and JWT token utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*, False otherwise."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    """
    Encode *data* as a signed JWT.

    An ``exp`` claim is added automatically using
    ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    payload = dict(data)
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate *token*.

    Raises ``jose.JWTError`` if the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
