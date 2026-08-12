# backend/app/core/security.py（密码哈希部分）
from passlib.context import CryptContext

# bcrypt 密码哈希上下文：
# - schemes=["bcrypt"]  只使用 bcrypt 算法进行哈希
# - deprecated="auto"   自动检测并处理被弃用的旧哈希格式
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """对明文密码进行 bcrypt 哈希，返回可直接存入数据库的哈希串。

    每次哈希都会生成随机 salt，因此同一密码两次哈希结果不同。
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码与数据库中的哈希串是否匹配。

    - plain_password: 用户登录时输入的明文密码
    - password_hash:  数据库中存储的哈希串
    匹配返回 True，不匹配返回 False（不抛出异常）。
    """
    return pwd_context.verify(plain_password, password_hash)
