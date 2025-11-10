import os
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import uuid


def _get_env(name: str, default: Optional[str] = None) -> str:
    value = os.environ.get(name)
    if value:
        return value
    if default is not None:
        return default
    raise RuntimeError(f"缺少环境变量: {name}")


def get_client() -> QdrantClient:
    url = _get_env("QDRANT_URL")
    api_key = _get_env("QDRANT_API_KEY")
    return QdrantClient(url=url, api_key=api_key)


def get_collection_name() -> str:
    return os.environ.get("QDRANT_COLLECTION", "se_flows")


def ensure_collection(size: int = 1024, distance: str = "cosine") -> None:
    client = get_client()
    collection = get_collection_name()
    existing = {c.name for c in client.get_collections().collections}
    if collection not in existing:
        client.create_collection(
            collection_name=collection,
            vectors_config=rest.VectorParams(
                size=size,
                distance=getattr(rest.Distance, distance.upper()),
            ),
        )


def insert_points(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = get_client()
    collection = get_collection_name()
    points = []
    for it in items:
        pid = it.get("id")
        vec = it.get("vector")
        payload = it.get("payload") or {}

        # Qdrant要求ID为无符号整数或UUID
        if isinstance(pid, int):
            point_id = pid
        elif isinstance(pid, str):
            try:
                point_id = str(uuid.UUID(pid))
            except Exception as e:
                raise ValueError(f"无效的点ID（需为UUID或整数）：{pid}") from e
        else:
            raise ValueError(f"无效的点ID类型：{type(pid)}")

        points.append(rest.PointStruct(id=point_id, vector=vec, payload=payload))
    op = client.upsert(collection_name=collection, points=points)
    return {"status": "ok", "upserted": len(points), "operation": op.status}


def search_points(query_vector: List[float], limit: int = 5, score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    client = get_client()
    collection = get_collection_name()
    hits = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
        score_threshold=score_threshold,
    )
    results = []
    for h in hits:
        results.append({
            "id": h.id,
            "score": h.score,
            "payload": h.payload,
        })
    return results