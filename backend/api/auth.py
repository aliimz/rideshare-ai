"""
Authentication endpoints: register, login, and current-user lookup.

Uses PostgreSQL via AsyncSession + UserRepository.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.core.security import create_access_token, hash_password, verify_password
from backend.db.database import get_db
from backend.db.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


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
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Create a new user account. Returns a JWT access token on success.

    Raises HTTP 409 if the email address is already registered.
    """
    repo = UserRepository(db)

    existing = await repo.find_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = await repo.create(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        role=body.role,
    )

    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, summary="Obtain a JWT token")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email and password. Returns a JWT access token.

    Raises HTTP 401 on invalid credentials.
    """
    repo = UserRepository(db)
    user = await repo.find_by_email(body.email)

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": str(user.role.value)}
    )
    return TokenResponse(access_token=token)


@router.get("/me", summary="Return the authenticated user's profile")
async def me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return public profile fields for the currently authenticated user.
    """
    user_id = int(current_user["sub"])
    repo = UserRepository(db)
    user = await repo.find_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found.",
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
    }
