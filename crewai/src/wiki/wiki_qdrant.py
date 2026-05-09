"""
Cliente Qdrant — colección wiki_knowledge.
Metadatos por punto: slug, title, topic, source_file, chunk_index, content_preview
"""
import uuid
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    ScoredPoint,
)
from src.config import get_settings

import structlog
log = structlog.get_logger()

WIKI_COLLECTION = "wiki_knowledge"


def _get_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
        https=False,
    )


def ensure_wiki_collection() -> None:
    """Crea la colección wiki_knowledge si no existe."""
    settings = get_settings()
    client = _get_client()

    existing = [c.name for c in client.get_collections().collections]
    if WIKI_COLLECTION not in existing:
        client.create_collection(
            collection_name=WIKI_COLLECTION,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        log.info("Colección wiki creada", collection=WIKI_COLLECTION)
    else:
        log.info("Colección wiki ya existe", collection=WIKI_COLLECTION)


def upsert_wiki_chunk(
    vector: list[float],
    slug: str,
    title: str,
    topic: str,
    source_file: str,
    chunk_index: int,
    content_preview: str,
) -> str:
    """Inserta un chunk de artículo wiki. Retorna el point_id."""
    client = _get_client()
    point_id = str(uuid.uuid4())

    payload = {
        "slug": slug,
        "title": title,
        "topic": topic,
        "source_file": source_file,
        "chunk_index": chunk_index,
        "content_preview": content_preview[:500],
        "minio_path": f"wiki-articles/{topic}/{slug}.md",
    }

    client.upsert(
        collection_name=WIKI_COLLECTION,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)]
    )
    return point_id


def search_wiki(
    query_vector: list[float],
    topic: Optional[str] = None,
    limit: int = 5,
    score_threshold: float = 0.45,
) -> list[ScoredPoint]:
    """Búsqueda semántica en wiki_knowledge."""
    client = _get_client()

    conditions = []
    if topic:
        conditions.append(
            FieldCondition(key="topic", match=MatchValue(value=topic))
        )

    query_filter = Filter(must=conditions) if conditions else None

    return client.search(
        collection_name=WIKI_COLLECTION,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=score_threshold,
    )


def delete_article_chunks(slug: str) -> None:
    """Elimina todos los chunks de un artículo wiki (para re-indexar)."""
    client = _get_client()
    client.delete(
        collection_name=WIKI_COLLECTION,
        points_selector=Filter(
            must=[FieldCondition(key="slug", match=MatchValue(value=slug))]
        )
    )
    log.info("Chunks wiki eliminados", slug=slug)
