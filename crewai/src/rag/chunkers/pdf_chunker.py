"""
Chunker de PDFs.
Gemini Embedding 2 acepta hasta 6 páginas por request.
Estrategia: chunks de texto (más eficiente) con fallback a páginas para PDFs escaneados.
"""
from pathlib import Path
from pypdf import PdfReader
from src.config import get_settings
from src.rag.chunkers.text_chunker import chunk_text


def extract_pdf_text(file_path: Path) -> list[dict]:
    """
    Extrae texto de un PDF página a página.
    Retorna lista de {page_num, text}.
    """
    reader = PdfReader(str(file_path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page_num": i + 1, "text": text.strip()})
    return pages


def chunk_pdf(file_path: Path) -> list[dict]:
    """
    Divide un PDF en chunks de texto con metadatos de página.
    Retorna lista de {chunk_text, start_page, end_page}.
    """
    settings = get_settings()
    pages_per_chunk = settings.pdf_pages_per_chunk

    pages = extract_pdf_text(file_path)

    if not pages:
        return []

    # Agrupar páginas en bloques y extraer texto
    result_chunks = []
    for i in range(0, len(pages), pages_per_chunk):
        page_group = pages[i: i + pages_per_chunk]
        combined_text = "\n\n".join(p["text"] for p in page_group)
        start_page = page_group[0]["page_num"]
        end_page = page_group[-1]["page_num"]

        # Sub-chunking del texto combinado si es muy largo
        text_chunks = chunk_text(combined_text)
        for tc in text_chunks:
            result_chunks.append({
                "chunk_text": tc,
                "start_page": start_page,
                "end_page": end_page,
            })

    return result_chunks
