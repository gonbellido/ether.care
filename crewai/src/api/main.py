"""
API principal EsoterSystem — CrewAI
Puerto 8000: API de agentes + ingesta RAG
"""
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.rag.ingestion_pipeline import ingest_document, SUPPORTED_EXTENSIONS
from src.rag.qdrant_store import ensure_collection, search_knowledge
from src.rag.embeddings import embed_query
from src.db.knowledge_db import list_documents, get_document_by_hash
from src.config import get_settings
from src.wiki.router import router as wiki_router
from src.wiki.wiki_qdrant import ensure_wiki_collection

import structlog
log = structlog.get_logger()

app = FastAPI(
    title="EsoterSystem API",
    description="Sistema multi-agente de consultoría espiritual — API interna",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.ether.care", "https://n8n.ether.care"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(wiki_router)


@app.on_event("startup")
async def startup():
    ensure_collection()
    ensure_wiki_collection()
    log.info("EsoterSystem API iniciada — colecciones Qdrant listas")


# ─── HEALTH ──────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "esotersystem-api"}


# ─── RAG: INGESTA DE DOCUMENTOS ──────────────────────────────

@app.post("/rag/ingest", summary="Subir documento al RAG")
async def ingest_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    esoteric_system: str = Form("bioneuroemocion"),
    description: str = Form(""),
    author: str = Form(""),
    tags: str = Form(""),           # CSV: "salud,emociones,bnemo"
):
    """
    Sube un documento y lo indexa en el RAG.
    Formatos: PDF, TXT, DOCX, MP3, WAV, MP4, MOV
    Categorías válidas: bioneuroemocion, general, otro

    El proceso corre en background — retorna inmediatamente con el doc_id.
    """
    # Validar extensión
    suffix = Path(file.filename).suffix.lower()
    all_exts = [e for exts in SUPPORTED_EXTENSIONS.values() for e in exts]
    if suffix not in all_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {suffix}. Permitidos: {all_exts}"
        )

    # Validar sistema esotérico
    valid_systems = ["bioneuroemocion", "general", "otro"]
    if esoteric_system not in valid_systems:
        raise HTTPException(
            status_code=400,
            detail=f"Sistema inválido. Opciones: {valid_systems}"
        )

    # Guardar archivo temporalmente
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / file.filename
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Procesar en background
    background_tasks.add_task(
        _run_ingestion,
        tmp_path=tmp_path,
        tmp_dir=tmp_dir,
        title=title,
        esoteric_system=esoteric_system,
        description=description,
        author=author,
        tags=tags_list,
    )

    return {
        "message": "Ingesta iniciada en background",
        "file": file.filename,
        "esoteric_system": esoteric_system,
    }


async def _run_ingestion(tmp_path, tmp_dir, **kwargs):
    try:
        result = await ingest_document(file_path=tmp_path, **kwargs)
        log.info("Ingesta completada en background", **result)
    except Exception as e:
        log.error("Error en ingesta background", error=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ─── RAG: BÚSQUEDA (para debug y admin) ──────────────────────

class SearchRequest(BaseModel):
    query: str
    esoteric_system: Optional[str] = None
    limit: int = 5

@app.post("/rag/search", summary="Buscar en la base de conocimiento")
async def search_endpoint(req: SearchRequest):
    """Búsqueda semántica en el RAG. Para debugging y panel de admin."""
    query_vector = embed_query(req.query)
    results = search_knowledge(
        query_vector=query_vector,
        esoteric_system=req.esoteric_system,
        limit=req.limit,
    )
    return {
        "query": req.query,
        "results": [
            {
                "score": round(r.score, 4),
                "content": r.payload.get("content_preview", "")[:200],
                "esoteric_system": r.payload.get("esoteric_system"),
                "chunk_purpose": r.payload.get("chunk_purpose"),
                "topics": r.payload.get("topics", []),
                "doc_id": r.payload.get("doc_id"),
            }
            for r in results
        ]
    }


# ─── RAG: LISTADO DE DOCUMENTOS ──────────────────────────────

@app.get("/rag/documents", summary="Listar documentos indexados")
async def list_documents_endpoint(
    esoteric_system: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    docs = await list_documents(
        esoteric_system=esoteric_system,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {"documents": docs, "total": len(docs)}
