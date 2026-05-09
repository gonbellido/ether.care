import os
import io
import asyncio
import logging
import subprocess as sp
import tempfile
from typing import Optional

import numpy as np
import soundfile as sf
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from kokoro import KPipeline
from faster_whisper import WhisperModel
import edge_tts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kokoro + Edge TTS + Whisper STT")

tts = KPipeline(lang_code='a')

VOICES = {
    # Kokoro — English (US)
    "en_us_female_bella":  {"voice": "af_bella",  "backend": "kokoro"},
    "en_us_female_sarah":  {"voice": "af_sarah",  "backend": "kokoro"},
    "en_us_female_nicole": {"voice": "af_nicole", "backend": "kokoro"},
    "en_us_female_sky":    {"voice": "af_sky",    "backend": "kokoro"},
    "en_us_male_adam":     {"voice": "am_adam",   "backend": "kokoro"},
    "en_us_male_michael":  {"voice": "am_michael","backend": "kokoro"},
    "en_us_male_liam":     {"voice": "am_liam",   "backend": "kokoro"},

    # Kokoro — English (UK)
    "en_gb_female_emma":   {"voice": "bf_emma",   "backend": "kokoro"},
    "en_gb_female_isabella":{"voice": "bf_isabella","backend": "kokoro"},
    "en_gb_male_george":   {"voice": "bm_george", "backend": "kokoro"},
    "en_gb_male_lewis":    {"voice": "bm_lewis",  "backend": "kokoro"},

    # Edge TTS — Spanish (Spain)
    "es_es_female_elvira": {"voice": "es-ES-ElviraNeural",  "backend": "edge"},
    "es_es_male_alvaro":   {"voice": "es-ES-AlvaroNeural",  "backend": "edge"},

    # Edge TTS — Spanish (Mexico)
    "es_mx_female_dalia":  {"voice": "es-MX-DaliaNeural",   "backend": "edge"},
    "es_mx_male_jorge":    {"voice": "es-MX-JorgeNeural",   "backend": "edge"},

    # Edge TTS — Spanish (Argentina)
    "es_ar_female_elena":  {"voice": "es-AR-ElenaNeural",   "backend": "edge"},
}

SR = 24000

whisper = WhisperModel("base", device="cpu", compute_type="int8")


@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    voice: str = Form("af_bella"),
    speed: float = Form(1.0),
    fmt: str = Form("wav"),
):
    voice = voice.strip()
    if voice not in VOICES:
        raise HTTPException(400, f"Unknown voice. Available: {sorted(VOICES.keys())}")

    cfg = VOICES[voice]
    speed = max(0.5, min(2.0, speed))
    fmt = fmt.lower()
    if fmt not in ("wav", "flac", "ogg", "mp3"):
        fmt = "wav"

    if cfg["backend"] == "kokoro":
        audio = await _kokoro_tts(text, cfg["voice"], speed)
        return _build_response(audio, SR, fmt)

    return await _edge_tts_handler(text, cfg["voice"], fmt)


async def _kokoro_tts(text: str, voice_id: str, speed: float) -> np.ndarray:
    loop = asyncio.get_event_loop()
    generator = await loop.run_in_executor(None, lambda: tts(text, voice=voice_id, speed=speed))
    chunks = [audio for _, _, audio in generator]
    if not chunks:
        raise HTTPException(500, "No audio generated")
    return np.concatenate(chunks)


async def _edge_tts_handler(text: str, voice_id: str, fmt: str) -> Response:
    communicate = edge_tts.Communicate(text, voice_id)

    mp3_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_data.write(chunk["data"])
    mp3_data.seek(0)

    if fmt == "mp3":
        return Response(content=mp3_data.read(), media_type="audio/mpeg")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(mp3_data.read())
        tmp_path = tmp.name

    try:
        if fmt == "wav":
            data, sr = sf.read(tmp_path)
            return _build_response(data, sr, "wav")

        result = sp.run(
            ["ffmpeg", "-i", tmp_path, "-f", fmt, "-loglevel", "error", "-"],
            capture_output=True, check=True,
        )
        return Response(content=result.stdout, media_type=f"audio/{fmt}")
    finally:
        os.unlink(tmp_path)


def _build_response(audio: np.ndarray, sr: int, fmt: str) -> Response:
    if fmt == "mp3":
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmppath = tmp.name
        try:
            sf.write(tmppath, audio, sr)
            result = sp.run(
                ["ffmpeg", "-i", tmppath, "-f", "mp3", "-loglevel", "error", "-"],
                capture_output=True, check=True,
            )
            return Response(content=result.stdout, media_type="audio/mpeg")
        finally:
            os.unlink(tmppath)

    buf = io.BytesIO()
    sf.write(buf, audio, sr, format=fmt.upper())
    buf.seek(0)
    return Response(content=buf.read(), media_type=f"audio/{fmt}")


@app.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = None,
):
    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    try:
        segments, info = whisper.transcribe(path, language=language or None)
        text = " ".join(s.text for s in segments)
        return {"text": text, "language": info.language, "duration": round(info.duration, 2)}
    finally:
        os.unlink(path)


@app.get("/voices")
async def list_voices():
    return {"voices": {k: v["voice"] for k, v in VOICES.items()}}


@app.get("/health")
async def health():
    return {"status": "ok"}
