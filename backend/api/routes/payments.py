# backend/api/routes/payments.py
"""
Payment routes — Razorpay (primary for Indian students)

Flow:
  1. POST /create-order   → Backend creates Razorpay order → returns {order_id, amount, key}
  2. Frontend opens Razorpay popup with these details
  3. User pays via UPI / card / net banking
  4. POST /verify-payment → Backend verifies HMAC signature → upgrades user tier
"""
import hmac
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.payment import Payment

router = APIRouter()
logger = logging.getLogger(__name__)

# Plan prices in paise (100 paise = ₹1)
PLAN_PRICES = {
    "pro":  {"amount": 9900,  "label": "Student Pro — ₹99/month"},
    "team": {"amount": 49900, "label": "Team Plan — ₹499/month"},
}


class CreateOrderRequest(BaseModel):
    plan: str = "pro"


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str = "pro"


@router.post("/create-order")
async def create_order(
    payload: CreateOrderRequest,
    user: User = Depends(get_current_user),
):
    """Create a Razorpay order. Frontend uses returned data to open payment popup."""
    if payload.plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan. Use 'pro' or 'team'.")

    if user.tier == payload.plan:
        raise HTTPException(status_code=400, detail=f"Already on {payload.plan} plan.")

    plan = PLAN_PRICES[payload.plan]

    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        order = client.order.create({
            "amount": plan["amount"],
            "currency": "INR",
            "receipt": f"rcpt_{user.id[:8]}",
            "notes": {"user_id": user.id, "user_email": user.email, "plan": payload.plan},
        })

        logger.info(f"Order created: {order['id']} for {user.email} ({payload.plan})")

        return {
            "order_id": order["id"],
            "amount": plan["amount"],
            "currency": "INR",
            "key": settings.RAZORPAY_KEY_ID,
            "plan_name": plan["label"],
            "user_name": user.name or "",
            "user_email": user.email,
        }

    except ImportError:
        raise HTTPException(status_code=500, detail="razorpay package not installed.")
    except Exception as e:
        logger.exception(f"Order creation failed: {e}")
        raise HTTPException(status_code=500, detail="Payment system error. Try again.")


@router.post("/verify-payment")
async def verify_payment(
    payload: VerifyPaymentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Razorpay payment using HMAC-SHA256 signature.
    
    How signature verification works:
    - Razorpay signs payments: HMAC_SHA256(order_id + "|" + payment_id, secret_key)
    - We compute the same hash with our secret key
    - If they match → payment is authentic
    - If not → someone tampered with the request → reject
    """
    message = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected != payload.razorpay_signature:
        logger.warning(f"Signature mismatch for user {user.email}")
        raise HTTPException(status_code=400, detail="Invalid payment signature.")

    # Prevent duplicate processing
    dup = await db.execute(
        select(Payment).where(Payment.provider_id == payload.razorpay_payment_id)
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Payment already processed.")

    # Upgrade user
    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one()
    db_user.tier = payload.plan

    # Record payment
    db.add(Payment(
        user_id=user.id,
        amount_cents=PLAN_PRICES.get(payload.plan, {}).get("amount", 9900),
        currency="INR",
        provider="razorpay",
        provider_id=payload.razorpay_payment_id,
        status="success",
        plan=payload.plan,
    ))
    await db.commit()

    logger.info(f"User {user.email} → upgraded to {payload.plan}")
    return {"success": True, "tier": payload.plan}


@router.get("/history")
async def payment_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .limit(20)
    )
    return [
        {"id": p.id, "amount": p.amount_cents / 100, "currency": p.currency,
         "plan": p.plan, "status": p.status, "date": p.created_at}
        for p in result.scalars().all()
    ]
