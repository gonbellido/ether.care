from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Meta
    meta_verify_token: str = ""
    meta_access_token: str = ""
    meta_whatsapp_phone_id: str = ""
    # Google Gemini
    google_api_key: str = ""

    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection: str = "esoter_knowledge"

    # PostgreSQL
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "esotersystem"
    postgres_user: str = ""
    postgres_password: str = ""

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""

    # MySQL (Diagnóstico)
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str = "diagnostico"
    mysql_user: str = "root"
    mysql_password: str = ""

    # LLMs
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    admin_api_key: str = ""
    kimi_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Embeddings
    embedding_model: str = "gemini-embedding-2-preview"
    embedding_dimensions: int = 3072       # Gemini Embedding 2 Preview dimensiones completas
    embedding_batch_size: int = 10         # chunks por batch a Gemini

    # Chunking
    chunk_size_text: int = 800             # caracteres por chunk de texto
    chunk_overlap: int = 150              # solapamiento entre chunks
    audio_chunk_seconds: int = 70         # segundos por chunk de audio (límite: 80s)
    video_chunk_seconds: int = 100        # segundos por chunk de vídeo (límite: 120s)
    pdf_pages_per_chunk: int = 5          # páginas por chunk de PDF (límite: 6)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
