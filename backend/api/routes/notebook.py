# backend/api/routes/notebook.py
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.assignment import Assignment

router = APIRouter()
logger = logging.getLogger(__name__)


class NotebookRequest(BaseModel):
    subject:          str
    topic:            str
    pages:            int             = 5
    subtopics:        list[str]       = []
    handwriting_style: Optional[str] = "casual"
    paper_type:       Optional[str]  = "notebook"
    include_diagrams: bool            = False
    include_examples: bool            = True
    name:             Optional[str]  = ""
    assignment_no:    Optional[str]  = "01"


async def run_notebook_job(
    assignment_id:     str,
    subject:           str,
    topic:             str,
    pages:             int,
    subtopics:         list,
    handwriting_style: str,
    paper_type:        str,
    include_diagrams:  bool,
    include_examples:  bool,
    name:              str,
    assignment_no:     str,
):
    """Background job — runs after API instantly returns to user."""
    from core.database import AsyncSessionLocal
    from services.ai_service import generate_notebook_content
    from services.pdf_service import build_notebook_pdf
    from services.storage_service import upload_file

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Assignment).where(Assignment.id == assignment_id)
            )
            assignment = result.scalar_one()

            # Step 1 — Generate notebook content via AI
            notebook_data = await generate_notebook_content(
                subject          = subject,
                topic            = topic,
                pages            = pages,
                subtopics        = subtopics,
                include_diagrams = include_diagrams,
                include_examples = include_examples,
            )
            assignment.sections_json = notebook_data

            # Step 2 — Build PDF
            pdf_bytes, page_count = await build_notebook_pdf(
                notebook_data     = notebook_data,
                handwriting_style = handwriting_style,
                paper_type        = paper_type,
                subject           = subject,
                name              = name,
                assignment_no     = assignment_no,
            )

            # Step 3 — Upload to Cloudinary
            filename = f"notebooks/{assignment_id}/output.pdf"
            pdf_url  = await upload_file(
                pdf_bytes, filename, content_type="application/pdf"
            )

            # Step 4 — Mark done
            assignment.pdf_url      = pdf_url
            assignment.page_count   = page_count
            assignment.status       = "done"
            assignment.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"Notebook {assignment_id} done → {pdf_url}")

        except Exception as e:
            logger.exception(f"Notebook {assignment_id} failed: {e}")
            try:
                result = await db.execute(
                    select(Assignment).where(Assignment.id == assignment_id)
                )
                assignment = result.scalar_one_or_none()
                if assignment:
                    assignment.status        = "failed"
                    assignment.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                pass


@router.post("/generate")
async def generate_notebook(
    payload:          NotebookRequest,
    background_tasks: BackgroundTasks,
    user:             User         = Depends(get_current_user),
    db:               AsyncSession = Depends(get_db),
):
    # Pro/Team only
    if user.tier not in ("pro", "team"):
        raise HTTPException(
            status_code=403,
            detail="Full Notebook Generator is a Pro feature. Upgrade to unlock.",
        )

    if payload.pages < 1 or payload.pages > 20:
        raise HTTPException(
            status_code=400,
            detail="Pages must be between 1 and 20.",
        )

    # Save assignment record
    assignment = Assignment(
        user_id           = user.id,
        question          = f"Notebook: {payload.topic}",
        subject           = payload.subject,
        handwriting_style = payload.handwriting_style,
        paper_type        = payload.paper_type,
        status            = "processing",
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    # Dispatch background job
    background_tasks.add_task(
        run_notebook_job,
        assignment_id     = assignment.id,
        subject           = payload.subject,
        topic             = payload.topic,
        pages             = payload.pages,
        subtopics         = payload.subtopics,
        handwriting_style = payload.handwriting_style or "casual",
        paper_type        = payload.paper_type or "notebook",
        include_diagrams  = payload.include_diagrams,
        include_examples  = payload.include_examples,
        name              = payload.name or "",
        assignment_no     = payload.assignment_no or "01",
    )

    return {
        "assignment_id": assignment.id,
        "status":        "processing",
        "pages":         payload.pages,
    }


@router.get("/{assignment_id}/status")
async def notebook_status(
    assignment_id: str,
    user:          User         = Depends(get_current_user),
    db:            AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment).where(
            Assignment.id      == assignment_id,
            Assignment.user_id == user.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Notebook not found")

    return {
        "status":     assignment.status,
        "pdf_url":    assignment.pdf_url,
        "page_count": assignment.page_count,
        "error":      assignment.error_message,
    }
