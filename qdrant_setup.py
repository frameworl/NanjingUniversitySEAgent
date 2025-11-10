import os
import sys

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams
except Exception as e:
    print("[ERROR] qdrant-client 未安装或导入失败:", e)
    sys.exit(1)


def main():
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    if not url:
        print("[ERROR] 缺少环境变量 QDRANT_URL")
        sys.exit(2)
    if not api_key:
        print("[ERROR] 缺少环境变量 QDRANT_API_KEY")
        sys.exit(3)

    client = QdrantClient(url=url, api_key=api_key)

    # 列出现有集合
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    print("现有集合:", ", ".join(names) if names else "<空>")

    # 如果不存在则创建 se_flows
    target = "se_flows"
    if target not in names:
        client.create_collection(
            collection_name=target,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        print("[OK] 已创建集合:", target)
    else:
        print("[SKIP] 集合已存在:", target)

    # 再次确认
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    print("最新集合:", ", ".join(names))


if __name__ == "__main__":
    main()