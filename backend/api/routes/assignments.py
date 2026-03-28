# backend/api/routes/assignments.py
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.assignment import Assignment
from models.usage import UsageLog

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    question: str
    subject: Optional[str] = "General"
    grade_level: Optional[str] = "college"
    handwriting_style: Optional[str] = "casual"
    paper_type: Optional[str] = "notebook"
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
    if user.tier in ("pro", "team"):
        return
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


# ── Background job — runs after FastAPI returns response to user ──────────────
async def run_assignment_job(
    assignment_id: str,
    question: str,
    subject: str,
    grade_level: str,
    handwriting_style: str,
    paper_type: str,
    font_name: str,
):
    """
    This runs in the background after the API instantly returns job_id to user.
    Does the heavy work: AI call → handwriting render → PDF → Cloudinary upload.
    """
    from core.database import AsyncSessionLocal
    from services.ai_service import generate_structured_answer
    from services.pdf_service import build_assignment_pdf
    from services.storage_service import upload_file

    logger.info(f"Starting background job for assignment {assignment_id}")

    async with AsyncSessionLocal() as db:
        try:
            # Get assignment from database
            result = await db.execute(
                select(Assignment).where(Assignment.id == assignment_id)
            )
            assignment = result.scalar_one()

            # Step 1 — AI generates structured answer
            structured = await generate_structured_answer(
                question=question,
                subject=subject,
                grade_level=grade_level,
            )
            assignment.generated_answer = structured.get("full_text", "")
            assignment.sections_json = structured
            assignment.has_diagram = structured.get("has_diagram", False)
            assignment.has_math = structured.get("has_math", False)

            # Step 2 — Render handwritten PDF
            pdf_bytes, page_count = await build_assignment_pdf(
                structured=structured,
                handwriting_style=handwriting_style,
                paper_type=paper_type,
                font_name=font_name,
            )

            # Step 3 — Upload to Cloudinary
            filename = f"assignments/{assignment_id}/output.pdf"
            pdf_url = await upload_file(
                pdf_bytes, filename, content_type="application/pdf"
            )

            # Step 4 — Mark as done
            assignment.pdf_url = pdf_url
            assignment.page_count = page_count
            assignment.status = "done"
            assignment.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"Assignment {assignment_id} completed → {pdf_url}")

        except Exception as e:
            logger.exception(f"Assignment {assignment_id} failed: {e}")
            try:
                result = await db.execute(
                    select(Assignment).where(Assignment.id == assignment_id)
                )
                assignment = result.scalar_one_or_none()
                if assignment:
                    assignment.status = "failed"
                    assignment.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                pass


@router.post("/generate")
async def generate_assignment(
    payload: GenerateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check free tier limit
    await check_usage(user, db)

    # Save assignment to database with status pending
    assignment = Assignment(
        user_id=user.id,
        question=payload.question,
        subject=payload.subject,
        grade_level=payload.grade_level,
        handwriting_style=payload.handwriting_style,
        paper_type=payload.paper_type,
        font_name=payload.font_name,
        status="processing",
    )
    db.add(assignment)
    await log_usage(user.id, "generate_assignment", db)
    await db.commit()
    await db.refresh(assignment)

    # Add job to background — FastAPI returns instantly, job runs after
    background_tasks.add_task(
        run_assignment_job,
        assignment_id=assignment.id,
        question=payload.question,
        subject=payload.subject or "General",
        grade_level=payload.grade_level or "college",
        handwriting_style=payload.handwriting_style or "casual",
        paper_type=payload.paper_type or "notebook",
        font_name=payload.font_name or "Caveat",
    )

    # Return immediately — frontend polls /status until done
    return {
        "assignment_id": assignment.id,
        "status": "processing",
    }


@router.get("/{assignment_id}/status")
async def get_status(
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.user_id == user.id,
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
            Assignment.id == assignment_id,
            Assignment.user_id == user.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Not found")

    await db.delete(assignment)
    await db.commit()
    return {"deleted": True}
