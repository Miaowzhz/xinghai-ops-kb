"""AI 服务调用边界：统一通过 DashScope OpenAI 兼容端点访问大模型与 Embedding。

- 大模型 qwen-plus：答案生成、意图识别、问题拆解（ChatOpenAI，流式）
- Embedding text-embedding-v3（1024 维）：文档 chunk 向量化

注：
1. langchain-openai 1.4.2 已无 DashScopeEmbeddings；其 OpenAIEmbeddings 会先用
   tiktoken/transformers 预分词再发送，而 DashScope 的 /embeddings 只接受原始字符串，
   故自实现 DashScopeEmbeddings（openai SDK 直连同一兼容端点，符合 Embeddings 接口）。
2. 惰性单例：空 API Key 时模块可正常导入（应用能启动），首次调用 AI 时才实例化；
   未配置 Key 会在首次调用时抛出 Missing credentials。
"""
from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.core.config import settings


class DashScopeEmbeddings(Embeddings):
    """直连 DashScope OpenAI 兼容端点的 Embedding（按 LangChain Embeddings 接口封装）。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        dimensions: int | None = None,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        kwargs: dict = {"model": self.model, "input": texts}
        if self.dimensions is not None:
            kwargs["dimensions"] = self.dimensions
        data = self._client.embeddings.create(**kwargs).data
        return [d.embedding for d in data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache
def get_llm() -> ChatOpenAI:
    """大模型实例：用于答案生成、意图识别、问题拆解。"""
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        streaming=True,
    )


@lru_cache
def get_embeddings() -> DashScopeEmbeddings:
    """Embedding 实例：用于文档 chunk 向量化（1024 维）。"""
    return DashScopeEmbeddings(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        model=settings.embedding_model,
        dimensions=settings.embedding_dim,
    )
