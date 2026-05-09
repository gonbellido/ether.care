"""
Cliente Gemini Embedding 2 — multimodal (texto, audio, vídeo, imagen, PDF)
Modelo: gemini-embedding-2-preview
Dimensiones: 1536 (MRL)
"""
import base64
import asyncio
from pathlib import Path
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from google import genai
from google.genai import types

from src.config import get_settings

import structlog
log = structlog.get_logger()


def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key)


def _task_prefix(task: str, content: str) -> str:
    """
    gemini-embedding-2-preview usa prefijos en lugar de task_type.
    task: 'retrieval_document' | 'retrieval_query' | 'classification' |
          'clustering' | 'question_answering' | 'fact_checking'
    """
    prefix_map = {
        "retrieval_document": "task: search result",
        "retrieval_query":    "task: search query",
        "classification":     "task: classification",
        "clustering":         "task: clustering",
        "question_answering": "task: question answering",
        "fact_checking":      "task: fact checking",
    }
    prefix = prefix_map.get(task, "task: search result")
    return f"{prefix} | query: {content}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def embed_text(text: str, task: str = "retrieval_document") -> list[float]:
    """Genera embedding de texto."""
    settings = get_settings()
    client = _get_client()

    prefixed = _task_prefix(task, text)

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=prefixed,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimensions
        )
    )
    return result.embeddings[0].values


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def embed_texts_batch(texts: list[str], task: str = "retrieval_document") -> list[list[float]]:
    """Genera embeddings de múltiples textos en batch."""
    settings = get_settings()
    client = _get_client()

    prefixed = [_task_prefix(task, t) for t in texts]

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=prefixed,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimensions
        )
    )
    return [e.values for e in result.embeddings]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def embed_audio_chunk(audio_path: Path) -> list[float]:
    """
    Genera embedding de un chunk de audio (≤ 80 segundos).
    Formatos soportados: MP3, WAV, AIFF, AAC, OGG, FLAC
    """
    settings = get_settings()
    client = _get_client()

    suffix = audio_path.suffix.lower()
    mime_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".aiff": "audio/aiff",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    mime_type = mime_map.get(suffix, "audio/mpeg")

    audio_bytes = audio_path.read_bytes()
    audio_b64 = base64.b64encode(audio_bytes).decode()

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=types.Content(
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=audio_b64
                    )
                )
            ]
        ),
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimensions
        )
    )
    return result.embeddings[0].values


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def embed_video_chunk(video_path: Path) -> list[float]:
    """
    Genera embedding de un chunk de vídeo (≤ 120 segundos).
    Formatos soportados: MP4, MOV, AVI, MKV
    """
    settings = get_settings()
    client = _get_client()

    suffix = video_path.suffix.lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska",
    }
    mime_type = mime_map.get(suffix, "video/mp4")

    video_bytes = video_path.read_bytes()
    video_b64 = base64.b64encode(video_bytes).decode()

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=types.Content(
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=video_b64
                    )
                )
            ]
        ),
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimensions
        )
    )
    return result.embeddings[0].values


def embed_query(query: str) -> list[float]:
    """Embedding para consultas del Advisor (task: retrieval_query)."""
    return embed_text(query, task="retrieval_query")
