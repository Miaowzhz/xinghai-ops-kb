import asyncio
from sqlalchemy import update
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.user import User

INITIAL_PASSWORD = "XhOps@2026"

async def main():
    new_hash = hash_password(INITIAL_PASSWORD)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(User).values(password_hash=new_hash)
        )
        await db.commit()
        print(f"已更新 {result.rowcount} 个用户的密码哈希，初始密码：{INITIAL_PASSWORD}")


asyncio.run(main())
