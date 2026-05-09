"""
Chunker de texto plano y documentos Word.
Divide el texto en chunks con solapamiento para preservar contexto.
"""
from pathlib import Path
from docx import Document as DocxDocument
from src.config import get_settings


def chunk_text(text: str) -> list[str]:
    """Divide texto en chunks con solapamiento."""
    settings = get_settings()
    size = settings.chunk_size_text
    overlap = settings.chunk_overlap

    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]

        # Si no es el último chunk, intentar cortar en un punto o salto de línea
        if end < len(text):
            cut = max(
                chunk.rfind(". "),
                chunk.rfind(".\n"),
                chunk.rfind("\n\n"),
            )
            if cut > size // 2:   # solo si el corte está en la segunda mitad
                chunk = chunk[:cut + 1]
                end = start + cut + 1

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap

    return chunks


def chunk_docx(file_path: Path) -> list[str]:
    """Extrae texto de un .docx y lo divide en chunks."""
    doc = DocxDocument(str(file_path))
    full_text = "\n\n".join(
        p.text for p in doc.paragraphs if p.text.strip()
    )
    return chunk_text(full_text)


def chunk_plain_text_file(file_path: Path) -> list[str]:
    """Lee un archivo .txt y lo divide en chunks."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return chunk_text(text)
