"""
Chunker de audio.
Gemini Embedding 2 acepta hasta 80 segundos por request.
Divide audios largos en segmentos de ~70s con solapamiento de 2s.
"""
import subprocess
from pathlib import Path
from src.config import get_settings

import structlog
log = structlog.get_logger()


def get_audio_duration(file_path: Path) -> float:
    """Obtiene duración en segundos usando ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def split_audio(file_path: Path, output_dir: Path) -> list[Path]:
    """
    Divide un archivo de audio en chunks de ~70s con ffmpeg.
    Retorna lista de paths de los chunks generados.
    """
    settings = get_settings()
    chunk_secs = settings.audio_chunk_seconds
    overlap = 2  # segundos de solapamiento entre chunks

    duration = get_audio_duration(file_path)
    if duration == 0:
        log.error("No se pudo determinar duración del audio", path=str(file_path))
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = []

    # Si el audio es corto, no necesita dividirse
    if duration <= chunk_secs:
        dest = output_dir / file_path.name
        import shutil
        shutil.copy(file_path, dest)
        return [dest]

    start = 0.0
    idx = 0
    while start < duration:
        out_path = output_dir / f"{file_path.stem}_chunk{idx:03d}{file_path.suffix}"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-t", str(chunk_secs),
            "-i", str(file_path),
            "-acodec", "copy",
            str(out_path)
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            chunks.append(out_path)
        else:
            log.error("Error splitting audio chunk", idx=idx, stderr=result.stderr.decode())

        start += chunk_secs - overlap
        idx += 1

    log.info("Audio dividido en chunks", total=len(chunks), source=file_path.name)
    return chunks
