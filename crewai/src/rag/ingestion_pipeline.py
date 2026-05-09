"""
Pipeline principal de ingesta RAG.
Orquesta: archivo → chunks → embeddings Gemini → clasificación → Qdrant + PostgreSQL
"""
import asyncio
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.config import get_settings
from src.rag.embeddings import embed_texts_batch, embed_audio_chunk, embed_video_chunk
from src.rag.qdrant_store import ensure_collection, upsert_chunk
from src.rag.motivational_classifier import classify_chunks_batch
from src.rag.chunkers.text_chunker import chunk_text, chunk_docx, chunk_plain_text_file
from src.rag.chunkers.pdf_chunker import chunk_pdf
from src.rag.chunkers.audio_chunker import split_audio
from src.rag.chunkers.video_chunker import split_video
from src.db.knowledge_db import (
    create_knowledge_document,
    update_document_status,
    save_motivational_chunk,
)

import structlog
log = structlog.get_logger()

SUPPORTED_EXTENSIONS = {
    "text":  [".txt", ".md"],
    "docx":  [".docx"],
    "pdf":   [".pdf"],
    "audio": [".mp3", ".wav", ".aiff", ".aac", ".ogg", ".flac"],
    "video": [".mp4", ".mov", ".avi", ".mkv"],
}


def _file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def _detect_type(file_path: Path) -> Optional[str]:
    ext = file_path.suffix.lower()
    for ftype, exts in SUPPORTED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


async def ingest_document(
    file_path: Path,
    title: str,
    esoteric_system: str,
    description: str = "",
    author: str = "",
    tags: list[str] = None,
) -> dict:
    """
    Pipeline completo de ingesta de un documento.
    Retorna resumen del proceso.
    """
    settings = get_settings()
    file_type = _detect_type(file_path)

    if not file_type:
        raise ValueError(f"Formato no soportado: {file_path.suffix}")

    file_hash = _file_hash(file_path)
    doc_id = str(uuid4())

    # Registrar en PostgreSQL como 'processing'
    await create_knowledge_document(
        doc_id=doc_id,
        title=title,
        source_filename=file_path.name,
        content_type=file_type if file_type not in ("docx",) else "text",
        esoteric_system=esoteric_system,
        file_size_bytes=file_path.stat().st_size,
        file_hash=file_hash,
        description=description,
        author=author,
        tags=tags or [],
    )

    await asyncio.to_thread(ensure_collection)
    log.info("Iniciando ingesta", doc_id=doc_id, file=file_path.name, type=file_type)

    try:
        point_ids = []

        # ── TEXTO / DOCX / PDF ──────────────────────────────────
        if file_type in ("text", "docx", "pdf"):
            if file_type == "text":
                chunks_text = chunk_plain_text_file(file_path)
                chunks_meta = [{"chunk_text": c} for c in chunks_text]
            elif file_type == "docx":
                chunks_text = chunk_docx(file_path)
                chunks_meta = [{"chunk_text": c} for c in chunks_text]
            else:  # pdf
                chunks_meta = chunk_pdf(file_path)
                chunks_text = [c["chunk_text"] for c in chunks_meta]

            log.info("Chunks generados", total=len(chunks_text))

            # Clasificar todos los chunks (motivacional o no)
            classifications = await asyncio.to_thread(classify_chunks_batch, chunks_text)

            # Generar embeddings en batches (con fallback individual si el batch falla)
            batch_size = settings.embedding_batch_size
            all_vectors = []
            total_batches = (len(chunks_text) + batch_size - 1) // batch_size
            for i in range(0, len(chunks_text), batch_size):
                batch = chunks_text[i:i + batch_size]
                batch_num = i // batch_size + 1
                try:
                    vectors = await asyncio.to_thread(embed_texts_batch, batch)
                    all_vectors.extend(vectors)
                    log.info("Embeddings generados", batch=batch_num, total=total_batches)
                except Exception as e:
                    log.warning("Batch fallido, intentando uno a uno", batch=batch_num, error=str(e))
                    for j, text in enumerate(batch):
                        try:
                            from src.rag.embeddings import embed_text
                            vec = await asyncio.to_thread(embed_text, text, "retrieval_document")
                            all_vectors.append(vec)
                        except Exception as e2:
                            log.error("Chunk fallido, usando vector cero", chunk=i+j, error=str(e2))
                            all_vectors.append([0.0] * settings.embedding_dimensions)

            # Insertar en Qdrant y registrar motivacionales en PostgreSQL
            for idx, (chunk_text_str, vector, classification) in enumerate(
                zip(chunks_text, all_vectors, classifications)
            ):
                is_motivational = classification.get("is_motivational", False)
                chunk_purpose = "motivational" if is_motivational else "knowledge"

                point_id = await asyncio.to_thread(
                    upsert_chunk,
                    vector=vector,
                    doc_id=doc_id,
                    content_preview=chunk_text_str,
                    source_type="text" if file_type != "pdf" else "pdf",
                    esoteric_system=esoteric_system,
                    chunk_purpose=chunk_purpose,
                    topics=classification.get("topics", []),
                    emotional_states=classification.get("emotional_states", []),
                    motivational_type=classification.get("motivational_type"),
                    depth_level=classification.get("depth_level", 1),
                    extra_metadata={
                        "start_page": chunks_meta[idx].get("start_page"),
                        "end_page": chunks_meta[idx].get("end_page"),
                    } if file_type == "pdf" else {},
                )
                point_ids.append(point_id)

                # Guardar en tabla de chunks motivacionales si aplica
                if is_motivational and classification.get("confidence", 0) >= 0.65:
                    await save_motivational_chunk(
                        document_id=doc_id,
                        qdrant_point_id=point_id,
                        content_preview=chunk_text_str[:300],
                        esoteric_system=esoteric_system,
                        topics=classification.get("topics", []),
                        emotional_states=classification.get("emotional_states", []),
                        motivational_type=classification.get("motivational_type", "inspiracion"),
                        depth_level=classification.get("depth_level", 1),
                        detection_score=classification.get("confidence", 0.0),
                    )

        # ── AUDIO ───────────────────────────────────────────────
        elif file_type == "audio":
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_chunks = split_audio(file_path, Path(tmpdir))
                log.info("Chunks de audio generados", total=len(audio_chunks))

                for idx, chunk_path in enumerate(audio_chunks):
                    vector = await asyncio.to_thread(embed_audio_chunk, chunk_path)
                    point_id = await asyncio.to_thread(upsert_chunk,
                        vector=vector,
                        doc_id=doc_id,
                        content_preview=f"[Audio] {title} — segmento {idx + 1}/{len(audio_chunks)}",
                        source_type="audio",
                        esoteric_system=esoteric_system,
                        chunk_purpose="knowledge",  # audio no se clasifica como motivacional automáticamente
                        extra_metadata={
                            "chunk_index": idx,
                            "total_chunks": len(audio_chunks),
                        }
                    )
                    point_ids.append(point_id)
                    log.info("Chunk audio embedido", idx=idx + 1, total=len(audio_chunks))

        # ── VÍDEO ───────────────────────────────────────────────
        elif file_type == "video":
            with tempfile.TemporaryDirectory() as tmpdir:
                video_chunks = split_video(file_path, Path(tmpdir))
                log.info("Chunks de vídeo generados", total=len(video_chunks))

                for idx, chunk_path in enumerate(video_chunks):
                    vector = await asyncio.to_thread(embed_video_chunk, chunk_path)
                    point_id = await asyncio.to_thread(upsert_chunk,
                        vector=vector,
                        doc_id=doc_id,
                        content_preview=f"[Vídeo] {title} — segmento {idx + 1}/{len(video_chunks)}",
                        source_type="video",
                        esoteric_system=esoteric_system,
                        chunk_purpose="knowledge",
                        extra_metadata={
                            "chunk_index": idx,
                            "total_chunks": len(video_chunks),
                        }
                    )
                    point_ids.append(point_id)
                    log.info("Chunk vídeo embedido", idx=idx + 1, total=len(video_chunks))

        # Marcar como indexado en PostgreSQL
        motivational_count = sum(
            1 for pid in point_ids
        )  # simplificado — la DB tiene el conteo real

        await update_document_status(
            doc_id=doc_id,
            status="indexed",
            chunk_count=len(point_ids),
            qdrant_point_ids=point_ids,
        )

        log.info("Ingesta completada", doc_id=doc_id, chunks=len(point_ids))
        return {
            "doc_id": doc_id,
            "status": "indexed",
            "chunks_total": len(point_ids),
            "file": file_path.name,
        }

    except Exception as e:
        log.error("Error en ingesta", doc_id=doc_id, error=str(e))
        await update_document_status(doc_id=doc_id, status="failed", error=str(e))
        raise
