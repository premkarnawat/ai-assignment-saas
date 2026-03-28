# backend/services/pdf_service.py
"""
PDF Generation Pipeline
  structured_answer → layout engine → handwriting render → PDF bytes
"""
import io
import sys
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Add handwriting engine to Python path ─────────────────────────────────────
# handwriting_renderer.py lives in backend/handwriting/ folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../handwriting"))


async def build_assignment_pdf(
    structured:        dict,
    handwriting_style: str = "casual",
    paper_type:        str = "notebook",
    font_name:         str = "Caveat",
    subject:           str = "",
    name:              str = "",
    assignment_no:     str = "01",
) -> tuple[bytes, int]:
    """
    Convert structured AI answer into a handwritten PDF.

    Args:
        structured:        AI-generated structured answer dict
        handwriting_style: casual | neat | indie | architect
        paper_type:        notebook (only style now)
        font_name:         Caveat | PatrickHand | IndieFlower
        subject:           Subject name shown in header
        name:              Student name shown in header
        assignment_no:     Assignment number shown in header

    Returns:
        (pdf_bytes, page_count)
    """
    from handwriting_renderer import HandwritingRenderer, RendererConfig

    # Build text from structured AI response
    pages_text = _layout_to_pages(structured)

    # Configure renderer
    config = RendererConfig(
        font_name      = font_name,
        paper_type     = "notebook",   # Always notebook style
        base_font_size = _style_to_font_size(handwriting_style),
    )
    renderer = HandwritingRenderer(config)

    # Use title from AI response as subject if not provided
    if not subject:
        subject = structured.get("title", "Assignment")

    # Render all pages
    page_images = renderer.render_pages(
        pages_text    = pages_text,
        subject       = subject,
        name          = name,
        assignment_no = assignment_no,
    )

    # Assemble into PDF
    pdf_bytes = _images_to_pdf(page_images)
    return pdf_bytes, len(page_images)


async def build_notebook_pdf(
    notebook_data:     dict,
    handwriting_style: str = "casual",
    paper_type:        str = "notebook",
    subject:           str = "",
    name:              str = "",
    assignment_no:     str = "01",
) -> tuple[bytes, int]:
    """Build multi-page notebook PDF."""
    from handwriting_renderer import HandwritingRenderer, RendererConfig

    subject = subject or notebook_data.get("subject", "Notes")
    pages   = notebook_data.get("pages", [])

    config = RendererConfig(
        font_name      = "Caveat",
        paper_type     = "notebook",
        base_font_size = _style_to_font_size(handwriting_style),
    )
    renderer = HandwritingRenderer(config)

    all_images = []
    for i, page_data in enumerate(pages):
        content  = page_data.get("content", "")
        title    = page_data.get("title", "")
        page_num = page_data.get("page_number", i + 1)

        full_text = f"{title}\n\n{content}" if title else content

        img = renderer.render_page(
            text          = full_text,
            subject       = subject,
            page_num      = page_num,
            name          = name,
            assignment_no = assignment_no,
            is_first_page = (i == 0),
        )
        all_images.append(img)

    pdf_bytes = _images_to_pdf(all_images)
    return pdf_bytes, len(all_images)


def _layout_to_pages(structured: dict, chars_per_page: int = 1800) -> list[str]:
    """Split structured AI content into pages."""
    title    = structured.get("title", "Assignment")
    sections = structured.get("sections", [])

    full_content = f"{title}\n{'=' * min(len(title), 40)}\n\n"

    for section in sections:
        heading = section.get("heading", "")
        content = section.get("content", "")
        if heading:
            full_content += f"\n{heading}\n{'-' * min(len(heading), 30)}\n"
        full_content += f"{content}\n"

    # Split into pages by character count
    pages   = []
    current = ""
    for line in full_content.split("\n"):
        if len(current) + len(line) > chars_per_page and current:
            pages.append(current)
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        pages.append(current)

    return pages if pages else [full_content]


def _style_to_font_size(style: str) -> int:
    """Map handwriting style name to font size."""
    return {
        "casual":    26,
        "neat":      24,
        "indie":     27,
        "architect": 25,
    }.get(style, 26)


def _images_to_pdf(images: list) -> bytes:
    """Convert list of PIL Images to a single PDF."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.utils import ImageReader

        buf   = io.BytesIO()
        c     = rl_canvas.Canvas(buf, pagesize=A4)
        a4_w, a4_h = A4

        for img in images:
            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG", optimize=True)
            img_buf.seek(0)
            img_reader = ImageReader(img_buf)
            c.drawImage(img_reader, 0, 0, width=a4_w, height=a4_h)
            c.showPage()

        c.save()
        return buf.getvalue()

    except ImportError:
        # Fallback — Pillow PDF
        buf = io.BytesIO()
        if images:
            images[0].save(
                buf,
                format     = "PDF",
                save_all   = True,
                append_images = images[1:],
                resolution = 150,
            )
        return buf.getvalue()
