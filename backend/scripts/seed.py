#!/usr/bin/env python3
# backend/scripts/seed.py
"""Seed initial data into the database."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from core.security import hash_password
from models.user import User
from models.assignment import Assignment
from sqlalchemy import select


async def seed():
    print("🌱 Seeding database...")

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(User).where(User.email == "demo@writeai.com"))
        if result.scalar_one_or_none():
            print("✓ Database already seeded")
            return

        # Create demo user
        demo_user = User(
            email="demo@writeai.com",
            name="Demo User",
            hashed_password=hash_password("demo1234"),
            provider="email",
            tier="pro",
            is_verified=True,
        )
        db.add(demo_user)

        # Create admin user
        admin = User(
            email="admin@writeai.com",
            name="Admin",
            hashed_password=hash_password("admin1234"),
            provider="email",
            tier="team",
            is_verified=True,
        )
        db.add(admin)

        await db.commit()
        print("✓ Created demo user: demo@writeai.com / demo1234")
        print("✓ Created admin:     admin@writeai.com / admin1234")
        print("🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
