from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User

INITIAL_PASSWORD = "XhOps@2026"

# 独立脚本场景：直接创建会话，而不是通过 FastAPI 依赖（get_db 返回生成器）
db = SessionLocal()

try:
    new_hash = hash_password(INITIAL_PASSWORD)
    count = db.query(User).update({User.password_hash: new_hash})
    db.commit()
    print(f"已更新 {count} 个用户的密码哈希，初始密码：{INITIAL_PASSWORD}")
finally:
    db.close()