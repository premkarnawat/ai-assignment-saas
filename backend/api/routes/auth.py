# backend/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from core.database import get_db
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str
    name:     str


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    google_token: str
    name:         str
    email:        EmailStr
    avatar_url:   str = ""


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          dict


def user_dict(u: User) -> dict:
    return {
        "id":         u.id,
        "email":      u.email,
        "name":       u.name,
        "avatar_url": u.avatar_url,
        "tier":       u.tier,
    }


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    db:      AsyncSession = Depends(get_db),
):
    # Check email not already used
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate password length — warn user if too long before truncation
    if len(payload.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    user = User(
        email           = payload.email,
        name            = payload.name,
        hashed_password = hash_password(payload.password),
        provider        = "email",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token  = create_access_token(user.id),
        refresh_token = create_refresh_token(user.id),
        user          = user_dict(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user   = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(
        access_token  = create_access_token(user.id),
        refresh_token = create_refresh_token(user.id),
        user          = user_dict(user),
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    payload: GoogleAuthRequest,
    db:      AsyncSession = Depends(get_db),
):
    """Accept verified Google user info from frontend OAuth flow."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user   = result.scalar_one_or_none()

    if not user:
        user = User(
            email      = payload.email,
            name       = payload.name,
            avatar_url = payload.avatar_url,
            provider   = "google",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return TokenResponse(
        access_token  = create_access_token(user.id),
        refresh_token = create_refresh_token(user.id),
        user          = user_dict(user),
    )


@router.post("/refresh")
async def refresh_token(
    body: dict,
    db:   AsyncSession = Depends(get_db),
):
    token   = body.get("refresh_token", "")
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    return {
        "access_token": create_access_token(payload["sub"]),
        "token_type":   "bearer",
    }
