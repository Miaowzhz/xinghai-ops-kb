from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置中心，支持通过环境变量 / .env 覆盖默认值。"""

    # 基础信息
    app_name: str = "xinghai-ops-kb"
    api_prefix: str = "/api"

    # 数据库（MySQL，asyncmy 异步驱动）
    database_url: str = (
        "mysql+asyncmy://xinghai:Xinghai@123456@127.0.0.1:3306/xinghai_ops_kb?charset=utf8mb4"
    )

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 小时

    # Milvus
    milvus_uri: str = "http://127.0.0.1:19530"

    # DashScope / 阿里云百炼（API Key 配置在 .env，不提交代码库）
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
