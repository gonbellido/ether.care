# ============================================================
#  Esoter LiveKit Agent - Dockerfile
# ============================================================
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema necesarias para audio/LiveKit
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root
RUN useradd -m -u 1000 agent
WORKDIR /app

# Instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descarga modelos (Silero VAD) para evitar lag en el primer arranque
RUN python -c "from livekit.plugins import silero; silero.VAD.load()" || true

# Copia el código
COPY main.py .

# Permisos
RUN chown -R agent:agent /app
USER agent

# Arranca el worker en modo producción
CMD ["python", "main.py", "start"]
