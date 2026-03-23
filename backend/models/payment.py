# backend/models/payment.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="usd")
    provider: Mapped[str] = mapped_column(String(50))   # stripe | razorpay
    provider_id: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(50))     # pending | success | failed
    plan: Mapped[str] = mapped_column(String(50))       # pro | team
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="payments")
