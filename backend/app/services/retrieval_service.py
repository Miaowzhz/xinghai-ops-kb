# backend/app/services/retrieval_service.py
from pymilvus import MilvusClient
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.chunk import KgDocumentChunk  # Stage 3 创建
from app.models.document import KgDocument

COLLECTION = "ops_kb_chunks"   # Milvus collection（SSOT §5）
VECTOR_TOP_K = 20              # dense 向量召回 top 20
BM25_TOP_K = 20                # sparse BM25 召回 top 20
FINAL_TOP_K = 5                # 融合后取 top 5
MIN_RRF_SCORE = 0.01           # RRF 融合分 < 0.01 判定无可靠依据（拒答）

milvus = MilvusClient(uri=settings.MILVUS_URI)          # http://localhost:19530
embeddings = OpenAIEmbeddings(
    model="text-embedding-v3",
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    dimensions=1024,
)


async def hybrid_retrieve(
    db: AsyncSession,
    query: str,
    product_line: str | None = None,
    product_version: str | None = None,
) -> list[dict]:
    """Milvus 单引擎 hybrid_search（dense + sparse 两路召回，RRF 融合），回 MySQL 补齐全文。"""
    qv = await embeddings.aembed_query(query)
    expr = _build_filter(product_line, product_version)
    res = milvus.hybrid_search(
        collection_name=COLLECTION,
        reqs=[
            AnnSearchRequest(data=[qv], anns_field="dense", param={"metric_type": "COSINE"}, limit=VECTOR_TOP_K),
            AnnSearchRequest(data=[query], anns_field="sparse", param={"metric_type": "BM25"}, limit=BM25_TOP_K),
        ],
        ranker=RRFRanker(k=60),
        limit=FINAL_TOP_K,
        filter=expr,
        output_fields=["chunk_id"],
    )
    fused = [{"chunk_id": hit["entity"]["chunk_id"], "score": hit["distance"]} for hit in res[0]]
    return await _fill_content(db, fused)


def _build_filter(product_line: str | None, product_version: str | None) -> str | None:
    """拼 Milvus 标量过滤表达式，如: product_line == "ECS" and product_version == "V3.2" """
    parts = []
    if product_line:
        parts.append(f'product_line == "{product_line}"')
    if product_version:
        parts.append(f'product_version == "{product_version}"')
    return " and ".join(parts) if parts else None