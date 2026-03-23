# backend/services/storage_service.py
"""
File storage using Cloudinary.

Why Cloudinary:
- Free tier: 25 GB storage + 25 GB bandwidth/month
- No separate CDN setup needed — Cloudinary serves files via CDN automatically
- PDFs are uploaded as raw files (resource_type="raw")
- Returns a permanent public URL instantly after upload
- Free account at cloudinary.com — no credit card needed

Setup:
  1. Go to cloudinary.com → Sign up free
  2. Dashboard → copy Cloud Name, API Key, API Secret
  3. Add to .env: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
"""
import logging
import cloudinary
import cloudinary.uploader
from core.config import settings

logger = logging.getLogger(__name__)

# Configure Cloudinary once at import time
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,  # Always use HTTPS
)


async def upload_file(
    file_bytes: bytes,
    key: str,
    content_type: str = "application/pdf",
) -> str:
    """
    Upload a file to Cloudinary and return its public URL.

    Args:
        file_bytes: Raw bytes of the file (PDF in this case)
        key: Path-like identifier e.g. "assignments/abc123/output.pdf"
             Used as the public_id in Cloudinary
        content_type: MIME type of the file

    Returns:
        Permanent public HTTPS URL to the uploaded file

    How it works:
        - resource_type="raw" tells Cloudinary this is not an image/video
          but a raw file like PDF
        - public_id is the unique identifier — we use the key (path) for this
        - overwrite=True means re-uploading same key replaces the old file
        - Cloudinary returns a secure_url we can store in the database
    """
    # Remove .pdf extension from public_id — Cloudinary adds it automatically
    public_id = key.replace(".pdf", "").replace(".png", "").replace(".jpg", "")

    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            resource_type="raw",        # Required for PDFs and non-image files
            overwrite=True,
            folder="ai-assignments",    # Organizes files in Cloudinary dashboard
            use_filename=False,
            unique_filename=False,
        )

        public_url = result.get("secure_url")
        logger.info(f"Uploaded to Cloudinary: {public_id} → {public_url}")
        return public_url

    except Exception as e:
        logger.exception(f"Cloudinary upload failed for {key}: {e}")
        raise


async def delete_file(key: str):
    """
    Delete a file from Cloudinary by its public_id.
    Called when user deletes an assignment.
    """
    public_id = f"ai-assignments/{key.replace('.pdf', '')}"
    try:
        cloudinary.uploader.destroy(public_id, resource_type="raw")
        logger.info(f"Deleted from Cloudinary: {public_id}")
    except Exception as e:
        logger.warning(f"Cloudinary delete failed for {key}: {e}")


async def get_file_url(public_id: str) -> str:
    """
    Generate a Cloudinary URL for a given public_id.
    Useful if you need to regenerate a URL from a stored public_id.
    """
    from cloudinary.utils import cloudinary_url
    url, _ = cloudinary_url(public_id, resource_type="raw", secure=True)
    return url
