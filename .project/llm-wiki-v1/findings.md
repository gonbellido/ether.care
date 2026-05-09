# Findings: LLM Wiki en Hetzner

**Issue**: llm-wiki-v1
**Updated**: 2026-04-18

## Research

### Workflow de Karpathy (referencia)
El patrón consiste en un directorio `raw/` como fuente de verdad, un "compilador" LLM que transforma los documentos brutos en artículos estructurados con backlinks, y un agente consultivo que hace RAG sobre la wiki resultante. La wiki es navegable en Obsidian y consultable por lenguaje natural.

### MinIO como gestor documental
- MinIO es compatible con S3 API, lo que permite usar el nodo S3 de n8n directamente.
- Soporta notificaciones webhook nativas (bucket events → POST HTTP) — trigger ideal para el compiler.
- Imagen: `quay.io/minio/minio` (oficial). Consola en puerto 9001, API en 9000.
- `mc` (MinIO Client) disponible en la imagen para crear buckets y usuarios programáticamente.
- Variables de entorno clave: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SITE_NAME`.

### Nginx con MinIO
- El proxy para la API S3 (9000) requiere headers específicos: `proxy_set_header Host $host`, `proxy_set_header X-Real-IP $remote_addr`, `client_max_body_size 0` (para uploads grandes), `chunked_transfer_encoding off`.
- La consola (9001) requiere WebSocket upgrade (`proxy_http_version 1.1`, `Upgrade`, `Connection`).

### SSL
- El certificado wildcard `*.ether.care` de Cloudflare Origin Certificate ya instalado cubre `minio.ether.care` y `minio-console.ether.care` automáticamente. **No se necesita certbot.**
- Los CNAMEs en Cloudflare deben apuntar al mismo IP que el resto de subdominios (`95.217.217.222`), con Proxy (naranja) activado.

### Remotely Save (Obsidian ↔ MinIO)
- Plugin "Remotely Save" soporta S3 custom endpoint (compatible con MinIO).
- La carpeta raíz del vault se mapea al bucket. Para mapear solo `wiki-articles/`, configurar el `Remote Base Dir` del plugin a la subcarpeta correspondiente.
- Alternativa: usar bucket `wiki-articles` directamente como raíz del vault (más limpio).

### Colección Qdrant para la wiki
- Separar de `esoter_knowledge` (base de conocimiento esotérico) para evitar contaminación de búsquedas.
- Nueva colección: `wiki_knowledge` — mismas dimensiones (1536 MRL cosine) que la existente.
- Metadatos del chunk: `source_file`, `article_slug`, `chunk_index`, `topic`, `date`, `content_type`.

### LLM para el compiler
- **DeepSeek V3** — coste bajo, buen razonamiento estructural, JSON output. Adecuado para volumen.
- El prompt del compiler debe incluir el índice actual de la wiki (slugs + títulos) para generar `[[backlinks]]` coherentes.
- Temperatura recomendada: 0.3 (creatividad baja, estructura alta).

### Tabla PostgreSQL para metadatos wiki
- Nueva tabla `wiki_articles` en schema `public` (o schema `wiki` propio):
  ```sql
  CREATE TABLE wiki.articles (
    id          SERIAL PRIMARY KEY,
    slug        TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    topic       TEXT,
    source_file TEXT,
    minio_path  TEXT NOT NULL,  -- wiki-articles/{topic}/{slug}.md
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
  );
  ```

## Technical Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| MinIO en docker-compose (no servicio externo) | Evitar dependencia externa, reutilizar infraestructura Hetzner existente | 2026-04-18 |
| Colección Qdrant separada (`wiki_knowledge`) | Aislar búsquedas wiki de conocimiento esotérico del RAG existente | 2026-04-18 |
| DeepSeek V3 para compiler y agente wiki | Coste bajo para volumen; Claude disponible para consultas premium si se requiere | 2026-04-18 |
| Remotely Save (no Obsidian Git) | S3 nativo, sync bidireccional automático sin necesidad de git en el servidor | 2026-04-18 |
| NO certbot para SSL | Wildcard Cloudflare Origin Certificate `*.ether.care` ya cubre nuevos subdominios | 2026-04-18 |
| Tabla `wiki.articles` en PostgreSQL | Metadatos indexables para health check y deduplicación por hash de fuente | 2026-04-18 |

## Key Insights

- El evento MinIO es la pieza clave: conecta la carga de documentos con el compiler automáticamente sin polling.
- El índice de la wiki (lista de slugs + títulos) debe recuperarse antes de cada compilación para generar backlinks coherentes — es una llamada ligera a MinIO LIST.
- La deduplicación por hash evita recompilar el mismo documento si se sube dos veces.
- El health check no necesita LLM para detectar artículos huérfanos (es análisis de grafo de backlinks) — solo necesita LLM para identificar gaps temáticos.
