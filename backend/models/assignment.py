# backend/models/assignment.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Input
    question: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    grade_level: Mapped[str] = mapped_column(String(50), nullable=True, default="college")

    # Options
    handwriting_style: Mapped[str] = mapped_column(String(50), default="casual")
    paper_type: Mapped[str] = mapped_column(String(50), default="notebook")
    font_name: Mapped[str] = mapped_column(String(100), default="Caveat")

    # Generated content
    generated_answer: Mapped[str] = mapped_column(Text, nullable=True)
    sections_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    has_diagram: Mapped[bool] = mapped_column(default=False)
    has_math: Mapped[bool] = mapped_column(default=False)

    # Output
    pdf_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    thumbnail_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending | processing | done | failed
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    task_id: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="assignments")
