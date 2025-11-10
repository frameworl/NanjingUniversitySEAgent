import os
from qdrant_client import QdrantClient


def main():
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    collection = os.environ.get("QDRANT_COLLECTION", "se_flows")
    dim = int(os.environ.get("QDRANT_VECTOR_SIZE", "1024"))

    if not url or not api_key:
        print("[ERROR] 缺少 QDRANT_URL 或 QDRANT_API_KEY")
        return

    client = QdrantClient(url=url, api_key=api_key)

    # 这里使用零向量进行演示；真实场景请替换为文本嵌入向量
    query_vec = [0.0] * dim
    results = client.search(collection_name=collection, query_vector=query_vec, limit=5)

    print(f"搜索返回 {len(results)} 条：")
    for r in results:
        print({"id": r.id, "score": r.score, "payload": r.payload})


if __name__ == "__main__":
    main()