"""初始化 Milvus Collection、BM25 Function 和索引。

仅用于部署验收或本地重建。生产环境不要随意启用 drop_collection。
执行方式：在 backend 目录运行 `python -m scripts.init_milvus`。
"""

from pymilvus import DataType, Function, FunctionType

from app.core.milvus import COLLECTION, milvus_client


def init_collection() -> None:
    client = milvus_client

    # 已存在则先删除。仅部署验收阶段可这样做，生产环境禁止随意 drop。
    if client.has_collection(COLLECTION):
        client.drop_collection(COLLECTION)

    # 主键、文本字段、稀疏/稠密向量以及用于 metadata 过滤的字段。
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(
        "chunk_id",
        DataType.VARCHAR,
        max_length=64,
        is_primary=True,
    )
    schema.add_field(
        "content",
        DataType.VARCHAR,
        max_length=8192,
        enable_analyzer=True,
        analyzer_params={"type": "chinese"},
    )
    schema.add_field("sparse", DataType.SPARSE_FLOAT_VECTOR)
    schema.add_field("dense", DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field("product_line", DataType.VARCHAR, max_length=64)
    schema.add_field("product_version", DataType.VARCHAR, max_length=64)

    # 从 content 自动生成 BM25 稀疏向量，入库时不需要手写 sparse。
    bm25_function = Function(
        name="bm25",
        function_type=FunctionType.BM25,
        input_field_names=["content"],
        output_field_names=["sparse"],
    )
    schema.add_function(bm25_function)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="dense",
        index_type="FLAT",
        metric_type="COSINE",
    )
    index_params.add_index(
        field_name="sparse",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
    )

    client.create_collection(
        collection_name=COLLECTION,
        schema=schema,
        index_params=index_params,
    )

    print(client.list_collections())
    print(client.describe_collection(COLLECTION))


if __name__ == "__main__":
    init_collection()
