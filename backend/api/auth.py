"""
Authentication endpoints: register, login, and current-user lookup.

Uses an in-memory store (dict keyed by email) in place of a real database.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.core.dependencies import get_current_user
from backend.core.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# In-memory user store  {email: user_record}
# ---------------------------------------------------------------------------
_users: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=7)
    role: Literal["rider", "driver"] = "rider"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(body: RegisterRequest) -> TokenResponse:
    """
    Create a new user account.  Returns a JWT access token on success.

    Raises HTTP 409 if the email address is already registered.
    """
    if body.email in _users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_id = str(uuid.uuid4())
    user_record = {
        "id": user_id,
        "email": body.email,
        "full_name": body.full_name,
        "phone": body.phone,
        "role": body.role,
        "hashed_password": hash_password(body.password),
    }
    _users[body.email] = user_record

    token = create_access_token(
        {"sub": user_id, "email": body.email, "role": body.role}
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, summary="Obtain a JWT token")
def login(body: LoginRequest) -> TokenResponse:
    """
    Authenticate with email and password.  Returns a JWT access token.

    Raises HTTP 401 on invalid credentials.
    """
    user = _users.get(body.email)
    if user is None or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {"sub": user["id"], "email": user["email"], "role": user["role"]}
    )
    return TokenResponse(access_token=token)


@router.get("/me", summary="Return the authenticated user's profile")
def me(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Return public profile fields for the currently authenticated user.

    Raises HTTP 404 if the user record no longer exists (e.g. after a restart).
    """
    email = current_user.get("email")
    user = _users.get(email) if email else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found.",
        )

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "phone": user["phone"],
        "role": user["role"],
    }
