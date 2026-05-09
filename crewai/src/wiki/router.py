"""
Wiki API — endpoints para embedding y búsqueda en wiki_knowledge.
POST /wiki/embed  — chunking + embedding de un artículo wiki
POST /wiki/search — búsqueda semántica en wiki_knowledge
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.rag.chunkers.text_chunker import chunk_text
from src.rag.embeddings import embed_texts_batch, embed_query
from src.wiki.wiki_qdrant import ensure_wiki_collection, upsert_wiki_chunk, search_wiki, delete_article_chunks

import structlog
log = structlog.get_logger()

router = APIRouter(prefix="/wiki", tags=["wiki"])


class WikiEmbedRequest(BaseModel):
    text: str
    slug: str
    title: str
    topic: str = "general"
    source_file: str = ""
    overwrite: bool = True   # eliminar chunks anteriores del mismo slug antes de reinsertar


class WikiSearchRequest(BaseModel):
    query: str
    topic: Optional[str] = None
    limit: int = 5
    score_threshold: float = 0.45


@router.post("/embed", summary="Indexar artículo wiki en Qdrant")
async def embed_wiki_article(req: WikiEmbedRequest):
    """
    Recibe el contenido de un artículo wiki generado por el LLM compiler,
    lo divide en chunks, genera embeddings con Gemini y los indexa en
    la colección wiki_knowledge de Qdrant.
    """
    ensure_wiki_collection()

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="El campo 'text' está vacío")

    # Eliminar chunks anteriores del mismo artículo si se re-indexa
    if req.overwrite:
        delete_article_chunks(req.slug)

    chunks = chunk_text(req.text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No se generaron chunks del texto")

    # Embedding en batch (más eficiente que uno a uno)
    vectors = embed_texts_batch(chunks, task="retrieval_document")

    point_ids = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        pid = upsert_wiki_chunk(
            vector=vector,
            slug=req.slug,
            title=req.title,
            topic=req.topic,
            source_file=req.source_file,
            chunk_index=i,
            content_preview=chunk,
        )
        point_ids.append(pid)

    log.info("Artículo wiki indexado", slug=req.slug, chunks=len(chunks))

    return {
        "slug": req.slug,
        "title": req.title,
        "topic": req.topic,
        "chunks_embedded": len(chunks),
        "collection": "wiki_knowledge",
    }


@router.post("/search", summary="Buscar en wiki_knowledge")
async def search_wiki_endpoint(req: WikiSearchRequest):
    """
    Búsqueda semántica en la wiki. Devuelve artículos relevantes con
    el minio_path para que el agente pueda recuperar el .md completo.
    """
    query_vector = embed_query(req.query)
    results = search_wiki(
        query_vector=query_vector,
        topic=req.topic,
        limit=req.limit,
        score_threshold=req.score_threshold,
    )

    return {
        "query": req.query,
        "results": [
            {
                "score": round(r.score, 4),
                "slug": r.payload.get("slug"),
                "title": r.payload.get("title"),
                "topic": r.payload.get("topic"),
                "minio_path": r.payload.get("minio_path"),
                "content_preview": r.payload.get("content_preview", "")[:300],
            }
            for r in results
        ],
    }
