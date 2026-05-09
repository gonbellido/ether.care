"""
Operaciones de base de datos para la base de conocimiento.
Interactúa con las tablas knowledge_documents y knowledge_chunks_motivational.
"""
import asyncpg
from typing import Optional
from src.config import get_settings

import structlog
log = structlog.get_logger()


async def _get_conn():
    settings = get_settings()
    return await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


async def create_knowledge_document(
    doc_id: str,
    title: str,
    source_filename: str,
    content_type: str,
    esoteric_system: str,
    file_size_bytes: int,
    file_hash: str,
    description: str = "",
    author: str = "",
    tags: list = None,
) -> None:
    conn = await _get_conn()
    try:
        await conn.execute("""
            INSERT INTO knowledge_documents
                (id, title, source_filename, content_type, esoteric_system,
                 file_size_bytes, file_hash, description, author, tags,
                 processing_status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'processing')
            ON CONFLICT (id) DO NOTHING
        """,
            doc_id, title, source_filename, content_type, esoteric_system,
            file_size_bytes, file_hash, description, author, tags or []
        )
    finally:
        await conn.close()


async def update_document_status(
    doc_id: str,
    status: str,
    chunk_count: int = None,
    qdrant_point_ids: list = None,
    error: str = None,
) -> None:
    conn = await _get_conn()
    try:
        import json
        from datetime import datetime, timezone

        if status == "indexed":
            await conn.execute("""
                UPDATE knowledge_documents
                SET processing_status = $1,
                    chunk_count = $2,
                    qdrant_collection = $3,
                    qdrant_point_ids = $4::jsonb,
                    indexed_at = $5
                WHERE id = $6
            """,
                status, chunk_count, "esoter_knowledge",
                json.dumps(qdrant_point_ids or []),
                datetime.now(timezone.utc), doc_id
            )
        elif status == "failed":
            await conn.execute("""
                UPDATE knowledge_documents
                SET processing_status = $1, processing_error = $2
                WHERE id = $3
            """, status, error, doc_id)
        else:
            await conn.execute("""
                UPDATE knowledge_documents
                SET processing_status = $1 WHERE id = $2
            """, status, doc_id)
    finally:
        await conn.close()


async def save_motivational_chunk(
    document_id: str,
    qdrant_point_id: str,
    content_preview: str,
    esoteric_system: str,
    topics: list,
    emotional_states: list,
    motivational_type: str,
    depth_level: int,
    detection_score: float,
) -> None:
    conn = await _get_conn()
    try:
        await conn.execute("""
            INSERT INTO knowledge_chunks_motivational
                (document_id, qdrant_point_id, content_preview, esoteric_system,
                 topics, emotional_states, motivational_type, depth_level,
                 detection_method, detection_score)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'auto',$9)
        """,
            document_id, qdrant_point_id, content_preview, esoteric_system,
            topics, emotional_states, motivational_type, depth_level, detection_score
        )
    finally:
        await conn.close()


async def get_document_by_hash(file_hash: str) -> Optional[dict]:
    """Verifica si un documento ya fue indexado (deduplicación)."""
    conn = await _get_conn()
    try:
        row = await conn.fetchrow("""
            SELECT id, title, processing_status
            FROM knowledge_documents
            WHERE file_hash = $1 AND deleted_at IS NULL
        """, file_hash)
        return dict(row) if row else None
    finally:
        await conn.close()


async def list_documents(
    esoteric_system: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conn = await _get_conn()
    try:
        conditions = ["deleted_at IS NULL"]
        params = []
        idx = 1

        if esoteric_system:
            conditions.append(f"esoteric_system = ${idx}")
            params.append(esoteric_system)
            idx += 1
        if status:
            conditions.append(f"processing_status = ${idx}")
            params.append(status)
            idx += 1

        where = " AND ".join(conditions)
        params += [limit, offset]

        rows = await conn.fetch(f"""
            SELECT id, title, content_type, esoteric_system, processing_status,
                   chunk_count, motivational_chunk_count, created_at
            FROM knowledge_documents
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx+1}
        """, *params)
        return [dict(r) for r in rows]
    finally:
        await conn.close()
