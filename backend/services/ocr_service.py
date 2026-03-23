# backend/services/ocr_service.py
import asyncio
import io
import logging
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


def _preprocess_image(image_bytes: bytes) -> Image.Image:
    """Enhance image for better OCR accuracy."""
    img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale

    # Upscale small images
    w, h = img.size
    if w < 1000:
        scale = 1000 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Enhance contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    return img


async def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image using Tesseract OCR.
    Runs in thread pool to avoid blocking async event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_sync, image_bytes)


def _extract_sync(image_bytes: bytes) -> str:
    try:
        import pytesseract
        img = _preprocess_image(image_bytes)
        # PSM 6 = Assume uniform block of text
        config = "--psm 6 --oem 3"
        text = pytesseract.image_to_string(img, config=config, lang="eng")
        return text.strip()
    except ImportError:
        logger.error("pytesseract not installed. Run: pip install pytesseract")
        return ""
    except Exception as e:
        logger.exception(f"OCR failed: {e}")
        return ""
