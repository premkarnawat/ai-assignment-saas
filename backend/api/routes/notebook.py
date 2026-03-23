# backend/api/routes/notebook.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.assignment import Assignment
from models.usage import UsageLog
from workers.tasks import process_notebook

router = APIRouter()


class NotebookRequest(BaseModel):
    subject: str
    topic: str
    pages: int = 5
    subtopics: Optional[list[str]] = None
    handwriting_style: Optional[str] = "casual"
    paper_type: Optional[str] = "notebook"
    include_diagrams: bool = True
    include_examples: bool = True


@router.post("/generate")
async def generate_notebook(
    payload: NotebookRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.tier == "free":
        raise HTTPException(
            status_code=403,
            detail="Full Notebook Generator is a Pro feature. Upgrade to unlock.",
        )

    # Cap pages
    pages = min(payload.pages, 20)

    assignment = Assignment(
        user_id=user.id,
        question=f"[NOTEBOOK] {payload.subject}: {payload.topic}",
        subject=payload.subject,
        handwriting_style=payload.handwriting_style,
        paper_type=payload.paper_type,
        status="pending",
    )
    db.add(assignment)
    log = UsageLog(user_id=user.id, action="generate_notebook")
    db.add(log)
    await db.commit()
    await db.refresh(assignment)

    task = process_notebook.delay(
        assignment_id=assignment.id,
        subject=payload.subject,
        topic=payload.topic,
        pages=pages,
        subtopics=payload.subtopics or [],
        handwriting_style=payload.handwriting_style or "casual",
        paper_type=payload.paper_type or "notebook",
        include_diagrams=payload.include_diagrams,
        include_examples=payload.include_examples,
    )

    assignment.task_id = task.id
    assignment.status = "processing"
    await db.commit()

    return {
        "assignment_id": assignment.id,
        "task_id": task.id,
        "status": "processing",
        "estimated_seconds": pages * 8,
    }
