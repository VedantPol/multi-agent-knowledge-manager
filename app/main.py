from __future__ import annotations

from pathlib import Path
import logging

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.agents.workflow import build_workflow
from app.config import get_settings
from app.demo_data import DEMO_DOCUMENTS, SAMPLE_QUESTIONS
from app.memory import release_memory
from app.models import AskRequest, AskResponse, DemoLoadResponse, DocumentCreate, DocumentOut
from app.storage import KnowledgeStore


settings = get_settings()
store = KnowledgeStore(settings.database_path)
workflow = build_workflow(store)
logger = logging.getLogger("mak")

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

MEMORY_CLEANUP_PATHS = {
    "/api/ask",
    "/api/demo/load",
    "/api/documents",
    "/api/documents/upload",
}


@app.middleware("http")
async def cleanup_after_heavy_requests(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in MEMORY_CLEANUP_PATHS or request.url.path.startswith("/api/documents/"):
        release_memory(request.url.path)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    if settings.app_env == "development":
        detail = str(exc)
    else:
        detail = "Unexpected server error. Check container logs with: docker logs mak"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.app_env}


@app.post("/api/admin/memory/collect")
async def collect_memory() -> dict:
    return release_memory("admin")


@app.get("/api/documents", response_model=list[DocumentOut])
async def list_documents() -> list[dict]:
    return store.list_documents()


@app.get("/api/sample-questions", response_model=list[str])
async def sample_questions() -> list[str]:
    return SAMPLE_QUESTIONS


@app.post("/api/demo/load", response_model=DemoLoadResponse)
async def load_demo_data() -> dict:
    added = 0
    skipped = 0
    for document in DEMO_DOCUMENTS:
        source_url = document["source_url"]
        if store.has_document_source(source_url):
            skipped += 1
            continue
        store.add_document(document["title"], document["content"], source_url)
        added += 1
    return {
        "added": added,
        "skipped": skipped,
        "total_documents": len(store.list_documents()),
        "sample_questions": SAMPLE_QUESTIONS,
    }


@app.post("/api/documents", response_model=DocumentOut)
async def create_document(payload: DocumentCreate) -> dict:
    if len(payload.content) > settings.max_upload_chars:
        raise HTTPException(status_code=413, detail="Document is larger than MAX_UPLOAD_CHARS.")
    return store.add_document(payload.title, payload.content, str(payload.source_url) if payload.source_url else None)


@app.post("/api/documents/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Only UTF-8 text uploads are supported.") from exc

    if len(content) > settings.max_upload_chars:
        raise HTTPException(status_code=413, detail="Document is larger than MAX_UPLOAD_CHARS.")

    title = file.filename or "Uploaded document"
    return store.add_document(title=title, content=content)


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int) -> dict:
    deleted = store.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted": True}


@app.post("/api/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> dict:
    result = await workflow.ainvoke({"question": payload.question, "top_k": payload.top_k})
    return {
        "question": payload.question,
        "answer": result.get("answer", ""),
        "citations": result.get("hits", []),
        "safety": result.get("safety"),
        "claims": result.get("claims", []),
        "hallucination_risk": result.get("hallucination_risk", "unknown"),
        "judge": result.get("judge_report"),
        "trace": result.get("trace", []),
    }


@app.get("/api/graph")
async def graph() -> dict:
    return {
        "nodes": ["guardrail", "planner", "retriever", "summarizer", "critic", "judge"],
        "edges": [
            ["START", "guardrail"],
            ["guardrail", "planner"],
            ["planner", "retriever"],
            ["retriever", "summarizer"],
            ["summarizer", "critic"],
            ["critic", "judge"],
            ["judge", "END"],
        ],
    }
