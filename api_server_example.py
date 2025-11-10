import os
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

# Qdrant 简单索引与检索支持
try:
    from qdrant_utils import ensure_collection, insert_points, search_points
    QDRANT_AVAILABLE = True
except Exception:
    QDRANT_AVAILABLE = False

app = FastAPI(title="NJU SE Agent API Example")


class AskRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    context_preferences: Optional[dict] = None


class ChecklistRequest(BaseModel):
    topic: str
    constraints: Optional[dict] = None


class CalendarRequest(BaseModel):
    title: str
    due: str
    assignees: Optional[List[str]] = None


# ---- Qdrant 索引/检索模型 ----
class VectorPoint(BaseModel):
    id: str
    vector: List[float]
    payload: Optional[dict] = None


class InsertRequest(BaseModel):
    points: List[VectorPoint]
    collection: Optional[str] = None  # 默认使用环境变量或 se_flows


class SearchRequest(BaseModel):
    vector: List[float]
    limit: int = 10
    collection: Optional[str] = None  # 默认使用环境变量或 se_flows


@app.get("/")
def root():
    return {"ok": True, "service": "NJU SE Agent API", "version": "v1"}


@app.post("/v1/ask")
def ask(body: AskRequest):
    # Stub response; integrate retrieval + rerank + generation in real implementation
    return {
        "answer": "这是一个示例回答：根据流程文档第3章需要提交开题报告与评审表。",
        "citations": [
            {
                "source": "se_manual_2024.pdf",
                "section_path": "第3章/3.2 开题要求",
                "version": "2024-fall",
            }
        ],
        "confidence": 0.87,
        "actions": [],
    }


@app.post("/v1/checklist")
def checklist(body: ChecklistRequest):
    items = [
        {"item": "查阅课程流程与模板", "status": "pending"},
        {"item": "填写开题报告（使用学院模板）", "status": "pending"},
        {"item": "安排评审时间并确认评审老师", "status": "pending"},
    ]
    return {"topic": body.topic, "items": items}


@app.post("/v1/calendar/create")
def calendar(body: CalendarRequest):
    return {
        "title": body.title,
        "due": body.due,
        "assignees": body.assignees or [],
        "id": "cal_123456",
        "status": "scheduled",
    }


@app.get("/v1/docs/source")
def doc_source(id: str = Query(..., description="文档ID")):
    return {
        "id": id,
        "download_url": f"https://example.com/docs/{id}",
        "type": "template",
    }


# 索引插入与检索模型
class IndexItem(BaseModel):
    id: str
    vector: List[float]
    payload: Optional[dict] = None


class IndexInsertRequest(BaseModel):
    items: List[IndexItem]


class SearchRequest(BaseModel):
    query_vector: List[float]
    limit: Optional[int] = 5
    score_threshold: Optional[float] = None


@app.post("/v1/index/insert")
def index_insert(body: IndexInsertRequest):
    if not QDRANT_AVAILABLE:
        return {"error": "qdrant 未可用，请安装依赖并配置环境变量"}
    try:
        ensure_collection(size=1024, distance="cosine")
        resp = insert_points([i.dict() for i in body.items])
        return {"ok": True, "upserted": resp.get("upserted", 0)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/v1/index/search")
def index_search(body: SearchRequest):
    if not QDRANT_AVAILABLE:
        return {"error": "qdrant 未可用，请安装依赖并配置环境变量"}
    try:
        ensure_collection(size=1024, distance="cosine")
        results = search_points(
            query_vector=body.query_vector,
            limit=body.limit or 5,
            score_threshold=body.score_threshold,
        )
        return {"ok": True, "hits": results}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---- Qdrant 插入与检索端点 ----
def _get_qdrant_client():
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    if not url or not api_key:
        raise RuntimeError("缺少 QDRANT_URL 或 QDRANT_API_KEY 环境变量")
    from qdrant_client import QdrantClient
    return QdrantClient(url=url, api_key=api_key)


def _ensure_collection(client, name: str, dim: int):
    from qdrant_client.http.models import Distance, VectorParams
    collections = client.get_collections().collections
    if any(c.name == name for c in collections):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )


@app.post("/v1/index/insert")
def index_insert(body: InsertRequest):
    from qdrant_client.http.models import PointStruct

    client = _get_qdrant_client()
    collection = body.collection or os.environ.get("QDRANT_COLLECTION", "se_flows")

    if not body.points:
        return {"ok": False, "error": "points 不能为空"}

    dim = len(body.points[0].vector)
    # 校验长度一致
    for p in body.points:
        if len(p.vector) != dim:
            return {"ok": False, "error": "所有向量维度必须一致"}

    _ensure_collection(client, collection, dim)

    points = [PointStruct(id=p.id, vector=p.vector, payload=p.payload or {}) for p in body.points]
    r = client.upsert(collection_name=collection, points=points)
    return {"ok": True, "collection": collection, "upserted": len(points), "status": getattr(r, "status", "ack")}


@app.post("/v1/index/search")
def index_search(body: SearchRequest):
    client = _get_qdrant_client()
    collection = body.collection or os.environ.get("QDRANT_COLLECTION", "se_flows")

    if not body.vector:
        return {"ok": False, "error": "vector 不能为空"}

    # 简化：不处理过滤器，直接基于向量检索
    results = client.search(collection_name=collection, query_vector=body.vector, limit=body.limit)
    items = [
        {
            "id": r.id,
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]
    return {"ok": True, "collection": collection, "count": len(items), "items": items}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)