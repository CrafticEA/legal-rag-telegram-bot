from fastapi import FastAPI
from pydantic import BaseModel

from indexer import build_index
from retriever import retrieve

app = FastAPI(title="RAG Service", version="0.1")

class BuildRequest(BaseModel):
    chat_id: str
    case_id: str
    docs: list[str]

class RetrieveRequest(BaseModel):
    chat_id: str
    case_id: str
    query: str
    top_k: int = 6

@app.post("/build")
def build(req: BuildRequest):
    stats = build_index(req.chat_id, req.case_id, req.docs)
    return {"status": "READY", "stats": stats}

@app.post("/retrieve")
def search(req: RetrieveRequest):
    case_path = f"data/cases/{req.chat_id}/{req.case_id}"
    results = retrieve(case_path, req.query, req.top_k)
    return {"chunks": results}

@app.get("/health")
def health():
    return {"service": "rag", "ok": True}