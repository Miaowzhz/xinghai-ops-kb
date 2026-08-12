from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., title="用户名", min_length=2, max_length=50)
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo