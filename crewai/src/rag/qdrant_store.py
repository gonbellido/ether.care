"""
Cliente Qdrant — operaciones de la base vectorial.
Colección única: esoter_knowledge
Metadatos por punto: doc_id, chunk_type, esoteric_system, topics,
                     emotional_states, motivational_type, depth_level,
                     content_preview, source_type, chunk_purpose
"""
import uuid
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, MatchAny,
    SearchRequest, ScoredPoint,
)
from src.config import get_settings

import structlog
log = structlog.get_logger()

COLLECTION_NAME = "esoter_knowledge"


def _get_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
        https=False,
    )


def ensure_collection() -> None:
    """Crea la colección si no existe."""
    settings = get_settings()
    client = _get_client()

    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        log.info("Colección Qdrant creada", collection=COLLECTION_NAME)
    else:
        log.info("Colección Qdrant ya existe", collection=COLLECTION_NAME)


def upsert_chunk(
    vector: list[float],
    doc_id: str,
    content_preview: str,
    source_type: str,           # text | audio | video | pdf
    esoteric_system: str,       # tarot | astrologia | etc.
    chunk_purpose: str,         # knowledge | motivational | both
    topics: list[str] = None,
    emotional_states: list[str] = None,
    motivational_type: str = None,
    depth_level: int = 1,
    extra_metadata: dict = None,
) -> str:
    """Inserta o actualiza un chunk en Qdrant. Retorna el point_id."""
    client = _get_client()
    point_id = str(uuid.uuid4())

    payload = {
        "doc_id": doc_id,
        "content_preview": content_preview[:500],
        "source_type": source_type,
        "esoteric_system": esoteric_system,
        "chunk_purpose": chunk_purpose,
        "topics": topics or [],
        "emotional_states": emotional_states or [],
        "motivational_type": motivational_type or "",
        "depth_level": depth_level,
    }
    if extra_metadata:
        payload.update(extra_metadata)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)]
    )
    return point_id


def search_knowledge(
    query_vector: list[float],
    esoteric_system: Optional[str] = None,
    chunk_purpose: Optional[str] = None,
    limit: int = 5,
    score_threshold: float = 0.6,
) -> list[ScoredPoint]:
    """
    Búsqueda semántica para el Advisor.
    Filtra opcionalmente por sistema esotérico y propósito del chunk.
    """
    client = _get_client()

    conditions = []
    if esoteric_system:
        conditions.append(
            FieldCondition(key="esoteric_system", match=MatchValue(value=esoteric_system))
        )
    if chunk_purpose:
        conditions.append(
            FieldCondition(key="chunk_purpose", match=MatchAny(any=[chunk_purpose, "both"]))
        )

    query_filter = Filter(must=conditions) if conditions else None

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=score_threshold,
    )
    return results


def search_motivational(
    query_vector: list[float],
    topics: list[str] = None,
    emotional_states: list[str] = None,
    depth_level: Optional[int] = None,
    exclude_point_ids: list[str] = None,
    limit: int = 3,
) -> list[ScoredPoint]:
    """
    Búsqueda semántica para el Follower — solo chunks motivacionales.
    Filtra por temas, estados emocionales y nivel de profundidad.
    Excluye puntos ya enviados al cliente.
    """
    client = _get_client()

    conditions = [
        FieldCondition(
            key="chunk_purpose",
            match=MatchAny(any=["motivational", "both"])
        )
    ]

    if depth_level:
        conditions.append(
            FieldCondition(key="depth_level", match=MatchValue(value=depth_level))
        )

    query_filter = Filter(must=conditions)

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit + (len(exclude_point_ids or [])),
        score_threshold=0.55,
    )

    # Filtrar los ya enviados
    if exclude_point_ids:
        results = [r for r in results if str(r.id) not in exclude_point_ids]

    return results[:limit]


def delete_doc_chunks(doc_id: str) -> int:
    """Elimina todos los chunks de un documento. Retorna cantidad eliminada."""
    client = _get_client()
    result = client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        )
    )
    log.info("Chunks eliminados de Qdrant", doc_id=doc_id)
    return result.operation_id
