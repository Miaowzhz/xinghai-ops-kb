"""Milvus 运行时客户端。"""

from pymilvus import MilvusClient

from app.config import settings


COLLECTION = "ops_kb_chunks"

# 惰性创建连接客户端；建表和建索引由 scripts/init_milvus.py 负责。
milvus_client = MilvusClient(uri=settings.MILVUS_URI)
