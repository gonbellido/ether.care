# Plan: LLM Wiki en Hetzner (ether.care)

**Issue**: llm-wiki-v1
**Phase**: implement
**Started**: 2026-04-18

## Goal

Implementar el workflow Karpathy de wiki auto-generada sobre la infraestructura Hetzner existente: MinIO como gestor documental, n8n como orquestador (compiler LLM + agente RAG), Obsidian como frontend local de captura y visualización.

## Approach

- **MinIO**: añadir al docker-compose.yml existente. Dos buckets: `wiki-raw/` (fuentes) y `wiki-articles/` (artículos generados).
- **Nginx**: añadir bloques para `minio.ether.care` (API :9000) y `minio-console.ether.care` (consola :9001). SSL cubierto por wildcard `*.ether.care` de Cloudflare ya instalado.
- **n8n Workflow 1 — Compiler**: MinIO webhook PUT en `wiki-raw/` → n8n descarga fichero → chunking Code JS (~800 tokens) → Gemini Embedding 2 → Qdrant → LLM genera artículo .md → MinIO PUT en `wiki-articles/`.
- **n8n Workflow 2 — Agente RAG**: HTTP trigger → embed pregunta → Qdrant top-5 → HTTP GET artículos de MinIO → LLM responde con contexto → respuesta con referencias.
- **n8n Workflow 3 — Health Check**: Cron nocturno → lista artículos en `wiki-articles/` → identifica huérfanos sin backlinks y gaps → informe .md en `queries/health/`.
- **Obsidian**: Remotely Save (backend S3 custom endpoint MinIO) sincroniza `wiki-articles/` con vault local.
- **LLM router**: DeepSeek V3 para compiler y agente (coste/volumen). Claude para consultas de alta calidad si se requiere.

## Implementation Steps

### Fase 1: MinIO — Infraestructura
- [ ] 1.1: Añadir servicio `minio` al `docker-compose.yml` en Hetzner (imagen `quay.io/minio/minio`, volumen `/data/minio`, puertos 9000/9001, env vars)
- [ ] 1.2: Añadir variables MinIO al `.env` (`MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SITE_NAME`)
- [ ] 1.3: Levantar MinIO (`docker-compose up -d minio`) y verificar healthcheck
- [ ] 1.4: Crear buckets `wiki-raw` y `wiki-articles` vía MinIO CLI (`mc`)
- [ ] 1.5: Crear usuario de servicio `n8n-wiki` con política read/write sobre ambos buckets
- [ ] 1.6: Crear credencial S3 en n8n (Access Key + Secret Key + endpoint `http://minio:9000`)

### Fase 2: Nginx + SSL
- [ ] 2.1: Añadir bloque `minio.ether.care` en nginx.conf (proxy_pass → minio:9000, headers S3)
- [ ] 2.2: Añadir bloque `minio-console.ether.care` en nginx.conf (proxy_pass → minio:9001, websocket upgrade)
- [ ] 2.3: Añadir CNAMEs en Cloudflare: `minio` y `minio-console` → IP Hetzner (o ya cubiertos por wildcard DNS)
- [ ] 2.4: Verificar que `https://minio.ether.care/minio/health/live` responde 200
- [ ] 2.5: Verificar que `https://minio-console.ether.care` carga la consola web

### Fase 3: MinIO Webhook → n8n
- [ ] 3.1: Configurar MinIO Event Rule en bucket `wiki-raw`: evento `s3:ObjectCreated:Put` → webhook `https://n8n.ether.care/webhook/wiki-ingest`
- [ ] 3.2: Crear workflow n8n "Wiki Ingest Trigger" con Webhook node (método POST, path `wiki-ingest`)
- [ ] 3.3: Añadir nodo Code para parsear el evento MinIO y extraer `bucket`, `object_key`, `content_type`
- [ ] 3.4: Probar subiendo un fichero .txt a `wiki-raw` y verificar que el webhook se dispara en n8n

### Fase 4: LLM Compiler (workflow principal)
- [ ] 4.1: Nodo HTTP GET → descargar fichero de MinIO (`http://minio:9000/wiki-raw/{object_key}`)
- [ ] 4.2: Nodo Code JS → chunker por tokens (~800 tokens, separadores: párrafos → frases)
- [ ] 4.3: Nodo HTTP Loop → Gemini Embedding 2 por chunk → insertar en Qdrant colección `wiki_knowledge` (metadatos: source, chunk_index, topic, date)
- [ ] 4.4: Nodo HTTP → recuperar índice actual de artículos de `wiki-articles/` (listado MinIO)
- [ ] 4.5: Nodo HTTP → DeepSeek V3: prompt compiler (genera artículo .md con frontmatter, resumen, secciones, [[backlinks]], tags)
- [ ] 4.6: Nodo HTTP PUT → subir artículo .md a MinIO `wiki-articles/{topic}/{slug}.md`
- [ ] 4.7: Nodo HTTP → insertar metadatos del artículo en PostgreSQL tabla `wiki_articles` (title, slug, source_file, topic, created_at)
- [ ] 4.8: Activar workflow y probar end-to-end con un PDF de tarot

### Fase 5: Agente RAG Consultivo
- [ ] 5.1: Crear workflow n8n "Wiki RAG Agent" con trigger HTTP (POST `/webhook/wiki-ask`)
- [ ] 5.2: Nodo HTTP → Gemini Embedding 2 sobre la pregunta
- [ ] 5.3: Nodo HTTP → Qdrant search en colección `wiki_knowledge` (top-5, score ≥ 0.45)
- [ ] 5.4: Nodo HTTP → GET artículos completos de MinIO a partir de los chunks recuperados
- [ ] 5.5: Nodo Code → formatear contexto (artículos + referencias)
- [ ] 5.6: Nodo HTTP → DeepSeek V3: respuesta con contexto + citas
- [ ] 5.7: (Opcional) Nodo HTTP PUT → guardar respuesta como .md en `wiki-articles/queries/{date}-{slug}.md`
- [ ] 5.8: Activar y probar con preguntas sobre documentos ya compilados

### Fase 6: Health Check Scheduler
- [ ] 6.1: Crear workflow n8n "Wiki Health Check" con trigger Cron (diario 03:00)
- [ ] 6.2: Nodo HTTP → listar todos los artículos en `wiki-articles/`
- [ ] 6.3: Nodo Code → parsear frontmatter + detectar artículos sin backlinks entrantes
- [ ] 6.4: Nodo HTTP → DeepSeek: identificar gaps temáticos en el índice
- [ ] 6.5: Nodo HTTP PUT → guardar informe .md en `wiki-articles/health/{date}-report.md`

### Fase 7: Obsidian Sync
- [ ] 7.1: Instalar plugin "Remotely Save" en Obsidian (versión con S3 custom endpoint)
- [ ] 7.2: Configurar: endpoint `https://minio.ether.care`, bucket `wiki-articles`, Access Key del usuario `n8n-wiki`
- [ ] 7.3: Sincronización inicial y verificar que los artículos generados aparecen en el vault
- [ ] 7.4: Instalar Obsidian Web Clipper para captura de webs → vault local raw/

## Current Step

**Fase 1** — Añadir MinIO al docker-compose.yml

## Blockers

- Acceso SSH al servidor Hetzner (el usuario lo tiene)
- Cloudflare DNS: verificar si wildcard `*.ether.care` ya cubre `minio` y `minio-console` (probablemente sí)

## Validation

- [ ] PDF subido a `wiki-raw/` → artículo .md en `wiki-articles/` en < 2 minutos
- [ ] Artículo incluye frontmatter válido, resumen 3 frases, secciones y al menos un `[[backlink]]`
- [ ] Artículo aparece en Obsidian tras sync
- [ ] Agente RAG responde preguntas con citas a artículos
- [ ] `https://minio.ether.care/minio/health/live` → 200
- [ ] `https://minio-console.ether.care` → consola web cargada
- [ ] Health check nocturno produce informe .md
