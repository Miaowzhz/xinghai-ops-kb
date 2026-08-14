from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, create_access_token
from app.models.user import User


# 校验用户
async def authenticate_user(db: AsyncSession, username: str, password: str) -> tuple[User, str] | None:
    """校验成功返回 (用户对象, token)，失败返回 None；账号停用抛 403。"""
    user = await db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    if user.status != "enabled":
        raise HTTPException(status_code=403, detail="账号已停用，请联系知识管理员")
    token = create_access_token(user_id=user.id, role=user.role)
    return user, token
