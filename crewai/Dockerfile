FROM python:3.12-slim

# Dependencias del sistema para procesamiento de audio/video
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    poppler-utils \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY crewai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente y canales
COPY crewai/src/ ./src/
COPY channels/ ./channels/

# Directorio para uploads temporales
RUN mkdir -p /app/uploads /app/logs

EXPOSE 8000 8001

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
