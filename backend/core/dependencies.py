"""
FastAPI dependency functions for authentication and role enforcement.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from backend.core.security import decode_token

_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    Decode the Bearer token from the ``Authorization`` header and return the
    embedded user payload dict.

    Raises HTTP 401 if the token is missing, malformed, or expired.
    """
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_rider(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow access only to users whose ``role`` claim is ``rider``."""
    if current_user.get("role") != "rider":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rider access required.",
        )
    return current_user


def require_driver(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow access only to users whose ``role`` claim is ``driver``."""
    if current_user.get("role") != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver access required.",
        )
    return current_user
