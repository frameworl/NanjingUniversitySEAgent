from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)