# backend/workers/tasks.py
import asyncio
import logging
from datetime import datetime, timezone

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run async coroutine from sync Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_assignment(
    self,
    assignment_id: str,
    question: str,
    subject: str,
    grade_level: str,
    handwriting_style: str,
    paper_type: str,
    font_name: str,
):
    """Main Celery task: AI generation → handwriting render → PDF upload."""
    logger.info(f"Processing assignment {assignment_id}")

    try:
        result = run_async(
            _process_assignment_async(
                assignment_id, question, subject, grade_level,
                handwriting_style, paper_type, font_name,
            )
        )
        return result
    except Exception as exc:
        logger.exception(f"Assignment {assignment_id} failed: {exc}")
        run_async(_mark_failed(assignment_id, str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_notebook(
    self,
    assignment_id: str,
    subject: str,
    topic: str,
    pages: int,
    subtopics: list,
    handwriting_style: str,
    paper_type: str,
    include_diagrams: bool,
    include_examples: bool,
):
    logger.info(f"Processing notebook {assignment_id}")
    try:
        result = run_async(
            _process_notebook_async(
                assignment_id, subject, topic, pages, subtopics,
                handwriting_style, paper_type, include_diagrams, include_examples,
            )
        )
        return result
    except Exception as exc:
        logger.exception(f"Notebook {assignment_id} failed: {exc}")
        run_async(_mark_failed(assignment_id, str(exc)))
        raise self.retry(exc=exc)


async def _process_assignment_async(
    assignment_id, question, subject, grade_level,
    handwriting_style, paper_type, font_name
):
    from core.database import AsyncSessionLocal
    from models.assignment import Assignment
    from sqlalchemy import select
    from services.ai_service import generate_structured_answer
    from services.pdf_service import build_assignment_pdf
    from services.storage_service import upload_file

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one()

        # Step 1: AI generates structured answer
        structured = await generate_structured_answer(
            question=question, subject=subject, grade_level=grade_level
        )
        assignment.generated_answer = structured.get("full_text", "")
        assignment.sections_json = structured
        assignment.has_diagram = structured.get("has_diagram", False)
        assignment.has_math = structured.get("has_math", False)

        # Step 2: Render handwritten PDF
        pdf_bytes, page_count = await build_assignment_pdf(
            structured=structured,
            handwriting_style=handwriting_style,
            paper_type=paper_type,
            font_name=font_name,
        )

        # Step 3: Upload to R2
        filename = f"assignments/{assignment_id}/output.pdf"
        pdf_url = await upload_file(pdf_bytes, filename, content_type="application/pdf")

        # Update assignment
        assignment.pdf_url = pdf_url
        assignment.page_count = page_count
        assignment.status = "done"
        assignment.completed_at = datetime.now(timezone.utc)
        await db.commit()

        return {"status": "done", "pdf_url": pdf_url}


async def _process_notebook_async(
    assignment_id, subject, topic, pages, subtopics,
    handwriting_style, paper_type, include_diagrams, include_examples
):
    from core.database import AsyncSessionLocal
    from models.assignment import Assignment
    from sqlalchemy import select
    from services.ai_service import generate_notebook_content
    from services.pdf_service import build_notebook_pdf
    from services.storage_service import upload_file

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one()

        # Generate multi-page notebook content via AI
        notebook_data = await generate_notebook_content(
            subject=subject,
            topic=topic,
            pages=pages,
            subtopics=subtopics,
            include_diagrams=include_diagrams,
            include_examples=include_examples,
        )

        assignment.sections_json = notebook_data

        # Build multi-page PDF
        pdf_bytes, page_count = await build_notebook_pdf(
            notebook_data=notebook_data,
            handwriting_style=handwriting_style,
            paper_type=paper_type,
        )

        filename = f"notebooks/{assignment_id}/output.pdf"
        pdf_url = await upload_file(pdf_bytes, filename, content_type="application/pdf")

        assignment.pdf_url = pdf_url
        assignment.page_count = page_count
        assignment.status = "done"
        assignment.completed_at = datetime.now(timezone.utc)
        await db.commit()

        return {"status": "done", "pdf_url": pdf_url}


async def _mark_failed(assignment_id: str, error: str):
    from core.database import AsyncSessionLocal
    from models.assignment import Assignment
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if assignment:
            assignment.status = "failed"
            assignment.error_message = error[:500]
            await db.commit()
