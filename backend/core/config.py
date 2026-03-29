# backend/core/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "AI Assignment Generator"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database (Neon PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/assignments"

    # Redis / Celery (Upstash Redis)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # JWT Auth
    JWT_SECRET: str = "change-this-to-32-random-chars-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # AI (Groq primary, OpenAI fallback)
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_PRIMARY: str = "llama-3.3-70b-versatile"
    AI_MODEL_FALLBACK: str = "gpt-4o-mini"

    # ── Cloudinary (File Storage) ─────────────────────────────────────────────
    # Get all three from: cloudinary.com → Dashboard → API Keys section
    # Free tier: 25 GB storage + 25 GB bandwidth/month — no credit card needed
    CLOUDINARY_CLOUD_NAME: str = ""   # e.g. "dxyz123abc"
    CLOUDINARY_API_KEY: str = ""      # e.g. "123456789012345"
    CLOUDINARY_API_SECRET: str = ""   # e.g. "AbCdEfGhIjKlMnOpQrStUvWxYz"

    # Payments (Razorpay)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Usage Limits
    FREE_DAILY_LIMIT: int = 3
    PRO_DAILY_LIMIT: int = 999999

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
