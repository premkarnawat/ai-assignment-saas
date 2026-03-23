# backend/api/routes/assignments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, date

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.assignment import Assignment
from models.usage import UsageLog
from workers.tasks import process_assignment

router = APIRouter()


class GenerateRequest(BaseModel):
    question: str
    subject: Optional[str] = "General"
    grade_level: Optional[str] = "college"
    handwriting_style: Optional[str] = "casual"   # casual | neat | indie | architect
    paper_type: Optional[str] = "notebook"         # notebook | exam | graph | white
    font_name: Optional[str] = "Caveat"


class AssignmentOut(BaseModel):
    id: str
    question: str
    subject: Optional[str]
    status: str
    pdf_url: Optional[str]
    thumbnail_url: Optional[str]
    page_count: int
    created_at: datetime

    class Config:
        from_attributes = True


async def check_usage(user: User, db: AsyncSession):
    if user.tier == "pro" or user.tier == "team":
        return  # unlimited

    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(func.sum(UsageLog.count)).where(
            and_(
                UsageLog.user_id == user.id,
                UsageLog.usage_date == today,
                UsageLog.action == "generate_assignment",
            )
        )
    )
    used = result.scalar() or 0
    if used >= settings.FREE_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Free tier limit reached ({settings.FREE_DAILY_LIMIT}/day). Upgrade to Pro.",
        )


async def log_usage(user_id: str, action: str, db: AsyncSession):
    log = UsageLog(user_id=user_id, action=action)
    db.add(log)


@router.post("/generate")
async def generate_assignment(
    payload: GenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await check_usage(user, db)

    assignment = Assignment(
        user_id=user.id,
        question=payload.question,
        subject=payload.subject,
        grade_level=payload.grade_level,
        handwriting_style=payload.handwriting_style,
        paper_type=payload.paper_type,
        font_name=payload.font_name,
        status="pending",
    )
    db.add(assignment)
    await log_usage(user.id, "generate_assignment", db)
    await db.commit()
    await db.refresh(assignment)

    # Dispatch Celery task
    task = process_assignment.delay(
        assignment_id=assignment.id,
        question=payload.question,
        subject=payload.subject or "General",
        grade_level=payload.grade_level or "college",
        handwriting_style=payload.handwriting_style or "casual",
        paper_type=payload.paper_type or "notebook",
        font_name=payload.font_name or "Caveat",
    )

    assignment.task_id = task.id
    assignment.status = "processing"
    await db.commit()

    return {"assignment_id": assignment.id, "task_id": task.id, "status": "processing"}


@router.get("/{assignment_id}/status")
async def get_status(
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id, Assignment.user_id == user.id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return {
        "status": assignment.status,
        "pdf_url": assignment.pdf_url,
        "thumbnail_url": assignment.thumbnail_url,
        "page_count": assignment.page_count,
        "error": assignment.error_message,
    }


@router.get("/", response_model=list[AssignmentOut])
async def list_assignments(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(Assignment)
        .where(Assignment.user_id == user.id)
        .order_by(Assignment.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id, Assignment.user_id == user.id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Not found")

    await db.delete(assignment)
    await db.commit()
    return {"deleted": True}
