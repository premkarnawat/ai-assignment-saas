# backend/api/routes/ocr.py
import base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user
from models.user import User
from services.ocr_service import extract_text_from_image

router = APIRouter()


@router.post("/extract")
async def extract_text(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    text = await extract_text_from_image(contents)
    return {"extracted_text": text, "char_count": len(text)}
