# Specification: LLM Wiki en Hetzner (ether.care)

**Issue**: llm-wiki-v1
**Status**: approved

## Overview

Sistema de wiki auto-generada siguiendo el workflow de Karpathy: documentos brutos entran al sistema, un LLM los "compila" en artículos .md interconectados con backlinks, y un agente RAG responde preguntas consultando esa wiki. MinIO actúa como gestor documental central. Obsidian es el frontend local de captura y visualización. Todo corre sobre la infraestructura Hetzner existente.

**Por qué**: el usuario necesita transformar fuentes heterogéneas (PDFs, webs clipeadas, transcripciones, imágenes) en una base de conocimiento estructurada, navegable y consultable mediante lenguaje natural, sin depender de servicios externos.

## Requirements

### Must Have
- [ ] MinIO integrado en docker-compose.yml existente con dos buckets: `wiki-raw/` y `wiki-articles/`
- [ ] Trigger automático en n8n cuando llega un fichero a `wiki-raw/` (MinIO webhook → n8n)
- [ ] Compiler LLM en n8n: chunking → embeddings en Qdrant → artículo .md generado con título, resumen, secciones, [[backlinks]] y frontmatter
- [ ] Artículos .md guardados en `wiki-articles/` en MinIO
- [ ] Agente consultivo RAG (trigger HTTP): embed pregunta → Qdrant top-5 → recuperar artículos de MinIO → respuesta con referencias
- [ ] Subdominios `minio.ether.care` y `minio-console.ether.care` con SSL (Cloudflare wildcard existente)
- [ ] Credencial MinIO S3 creada en n8n para lectura/escritura de buckets

### Should Have
- [ ] Sincronización Obsidian ↔ MinIO (`wiki-articles/`) vía Remotely Save (plugin S3)
- [ ] Scheduler nocturno (health check): detectar artículos huérfanos sin backlinks y gaps de conocimiento
- [ ] Respuestas del agente guardadas como .md en `queries/` (trazabilidad)
- [ ] Frontmatter de artículos con `topic`, `date`, `source`, `tags`
- [ ] Índice de la wiki inyectado en el prompt del compiler para generar backlinks coherentes

### Won't Have
- Autenticación de usuarios finales en la wiki (es una herramienta interna)
- Generación de sitio web público a partir de la wiki (fuera de alcance v1)
- Ingesta de vídeo directamente en este flujo (el pipeline RAG de CrewAI ya lo cubre)

## Acceptance Criteria

- [ ] Un PDF subido a `wiki-raw/` se convierte automáticamente en artículo .md en `wiki-articles/` en menos de 2 minutos
- [ ] El artículo generado incluye frontmatter válido, resumen de 3 frases, secciones y al menos un `[[backlink]]`
- [ ] El artículo aparece en Obsidian tras la siguiente sincronización de Remotely Save
- [ ] El agente RAG responde preguntas en lenguaje natural con citas a artículos fuente
- [ ] `minio.ether.care` y `minio-console.ether.care` cargan correctamente con SSL
- [ ] El health check nocturno produce un informe de artículos huérfanos y gaps

## User Stories

Como consultor esotérico, quiero subir un PDF de un libro de tarot y obtener automáticamente un artículo wiki estructurado, para que mi base de conocimiento crezca sin trabajo manual.

Como usuario de la wiki, quiero hacer una pregunta en lenguaje natural y recibir una respuesta con referencias a los artículos relevantes, para explorar el conocimiento sin tener que buscar manualmente.

Como administrador del sistema, quiero revisar cada noche qué artículos están aislados o qué conceptos faltan, para mantener la coherencia de la wiki.

## Edge Cases

| Case | Handling |
|------|----------|
| Fichero no soportado en wiki-raw/ | n8n devuelve error 422 y logea en PostgreSQL |
| LLM no genera JSON válido en el compiler | Retry con temperatura 0 y prompt simplificado |
| Qdrant sin chunks para una pregunta (score < 0.45) | Agente responde "no tengo información suficiente" + sugiere subir documentos |
| MinIO webhook falla / n8n offline | MinIO reintenta con backoff exponencial (configuración nativa) |
| Artículo duplicado (misma fuente reingestada) | Deduplicar por hash del fichero fuente antes de generar |
