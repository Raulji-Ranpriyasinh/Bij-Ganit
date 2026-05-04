import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password

async def create():
    async with AsyncSessionLocal() as db:
        user = User(
            name="Admin",
            email="admin@example.com",
            password=hash_password("password123"),
            role="admin"
        )
        db.add(user)
        await db.commit()
        print("✓ User created: admin@example.com / password123")

asyncio.run(create())