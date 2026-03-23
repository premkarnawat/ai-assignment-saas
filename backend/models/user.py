# backend/models/user.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="email")  # email | google
    provider_id: Mapped[str] = mapped_column(String(255), nullable=True)
    tier: Mapped[str] = mapped_column(String(50), default="free")  # free | pro | team
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assignments = relationship("Assignment", back_populates="user", lazy="dynamic")
    payments = relationship("Payment", back_populates="user", lazy="dynamic")
    usage_logs = relationship("UsageLog", back_populates="user", lazy="dynamic")
