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

# Add handwriting engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../handwriting-engine"))


async def build_assignment_pdf(
    structured: dict,
    handwriting_style: str = "casual",
    paper_type: str = "notebook",
    font_name: str = "Caveat",
) -> tuple[bytes, int]:
    """
    Convert structured AI answer into a handwritten PDF.
    Returns (pdf_bytes, page_count).
    """
    from handwriting_renderer import HandwritingRenderer, RendererConfig

    # 1. Build text content from sections
    pages_text = _layout_to_pages(structured)

    # 2. Configure renderer
    config = RendererConfig(
        font_name=font_name,
        paper_type=paper_type,
        base_font_size=_style_to_font_size(handwriting_style),
    )
    renderer = HandwritingRenderer(config)

    subject = structured.get("title", "Assignment")

    # 3. Render pages
    page_images = renderer.render_pages(pages_text, subject=subject)

    # 4. Handle diagrams
    if structured.get("has_diagram") and structured.get("diagram_mermaid"):
        try:
            diagram_img = await _render_mermaid(structured["diagram_mermaid"])
            if diagram_img:
                # Insert diagram page after first content page
                page_images.insert(1, diagram_img)
        except Exception as e:
            logger.warning(f"Diagram render failed: {e}")

    # 5. Assemble PDF
    pdf_bytes = _images_to_pdf(page_images)
    return pdf_bytes, len(page_images)


async def build_notebook_pdf(
    notebook_data: dict,
    handwriting_style: str = "casual",
    paper_type: str = "notebook",
) -> tuple[bytes, int]:
    """Build multi-page notebook PDF."""
    from handwriting_renderer import HandwritingRenderer, RendererConfig

    subject = notebook_data.get("subject", "Notes")
    pages = notebook_data.get("pages", [])

    config = RendererConfig(
        font_name="Caveat",
        paper_type=paper_type,
        base_font_size=_style_to_font_size(handwriting_style),
    )
    renderer = HandwritingRenderer(config)

    all_images = []
    for page_data in pages:
        content = page_data.get("content", "")
        title = page_data.get("title", "")
        page_num = page_data.get("page_number", 1)

        full_text = f"{title}\n\n{content}" if title else content
        img = renderer.render_page(
            full_text, subject=subject, page_num=page_num
        )
        all_images.append(img)

        # Diagram page
        if page_data.get("has_diagram") and page_data.get("diagram_mermaid"):
            try:
                diagram_img = await _render_mermaid(page_data["diagram_mermaid"])
                if diagram_img:
                    all_images.append(diagram_img)
            except Exception:
                pass

    pdf_bytes = _images_to_pdf(all_images)
    return pdf_bytes, len(all_images)


def _layout_to_pages(structured: dict, chars_per_page: int = 1800) -> list[str]:
    """Split structured content into pages."""
    title = structured.get("title", "Assignment")
    sections = structured.get("sections", [])

    full_content = f"{title}\n{'=' * min(len(title), 40)}\n\n"

    for section in sections:
        heading = section.get("heading", "")
        content = section.get("content", "")
        if heading:
            full_content += f"\n{heading}\n{'-' * min(len(heading), 30)}\n"
        full_content += f"{content}\n"

    # Split into pages
    pages = []
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
    return {
        "casual": 26,
        "neat": 24,
        "indie": 27,
        "architect": 25,
    }.get(style, 26)


def _images_to_pdf(images: list) -> bytes:
    """Convert list of PIL Images to PDF bytes using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as rl_canvas
        import tempfile

        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        a4_w, a4_h = A4

        for img in images:
            # Save image to temp buffer
            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG", optimize=True)
            img_buf.seek(0)

            # Scale image to A4
            from reportlab.lib.utils import ImageReader
            img_reader = ImageReader(img_buf)
            c.drawImage(img_reader, 0, 0, width=a4_w, height=a4_h)
            c.showPage()

        c.save()
        return buf.getvalue()

    except ImportError:
        # Fallback: return images as multi-page PDF using Pillow
        buf = io.BytesIO()
        if images:
            images[0].save(
                buf,
                format="PDF",
                save_all=True,
                append_images=images[1:],
                resolution=150,
            )
        return buf.getvalue()


async def _render_mermaid(mermaid_code: str):
    """Render Mermaid diagram to PIL Image. Requires mmdc CLI."""
    import subprocess
    import tempfile
    from PIL import Image

    try:
        with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
            f.write(mermaid_code)
            mmd_path = f.name

        out_path = mmd_path.replace(".mmd", ".png")
        result = subprocess.run(
            ["mmdc", "-i", mmd_path, "-o", out_path, "-w", "700", "-H", "400"],
            capture_output=True, timeout=30
        )
        if result.returncode == 0 and os.path.exists(out_path):
            return Image.open(out_path).convert("RGB")
    except Exception as e:
        logger.warning(f"Mermaid render failed: {e}")
    return None
