# backend/app/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/ 目录


def _load_env() -> None:
    """极简 .env 加载器：按 KEY=VALUE 逐行读入环境变量，已有的不覆盖。"""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()


class Settings:
    """全项目统一配置入口；新增配置项时在 .env 和这里各加一行。"""

    BASE_DIR: Path = BASE_DIR
    MYSQL_URL: str = os.environ["MYSQL_URL"]
    MILVUS_URI: str = os.environ["MILVUS_URI"]
    DASHSCOPE_API_KEY: str = os.environ["DASHSCOPE_API_KEY"]
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]
    JWT_EXPIRE_MINUTES: int = int(os.environ.get("JWT_EXPIRE_MINUTES", "720"))
    UPLOAD_DIR: str = os.environ.get("UPLOAD_DIR", "uploads")


settings = Settings()