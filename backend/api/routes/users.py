# backend/api/routes/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.assignment import Assignment
from models.usage import UsageLog

router = APIRouter()


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "tier": user.tier,
        "created_at": user.created_at,
    }


@router.get("/me/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()

    # Total assignments
    total_result = await db.execute(
        select(func.count()).where(Assignment.user_id == user.id)
    )
    total = total_result.scalar() or 0

    # Today's usage
    today_result = await db.execute(
        select(func.sum(UsageLog.count)).where(
            and_(
                UsageLog.user_id == user.id,
                UsageLog.usage_date == today,
            )
        )
    )
    today_usage = today_result.scalar() or 0

    limit = settings.FREE_DAILY_LIMIT if user.tier == "free" else settings.PRO_DAILY_LIMIT

    return {
        "total_assignments": total,
        "today_usage": today_usage,
        "daily_limit": limit,
        "remaining": max(0, limit - today_usage),
        "tier": user.tier,
    }
