from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services import auth_service
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# 登录
@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    result = authenticate_user(db, body.username, body.password)
    if result is None:
        # 不区分"用户不存在"和"密码错误"，避免暴露账号是否存在
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user, token = result
    return LoginResponse(
        access_token=token,
        user=UserInfo(id=user.id, username=user.username,
                      display_name=user.display_name, role=user.role),
    )


@router.get("/profile", response_model=UserInfo)
def profile(user: User = Depends(get_current_user)):
    return user