# Progress Log: EsoterSystem

## 2026-04-04 — Sesión 1: Kick-off y definición inicial

### Completado
- [x] Creado directorio del proyecto `/Documents/esotersystem`
- [x] Definida estructura de carpetas
- [x] Creado spec.md, plan.md, findings.md, CLAUDE.md, README.md
- [x] Definido modelo de datos CRM Espiritual (Cliente + Sesión)
- [x] Confirmado: infraestructura en Hetzner dedicado
- [x] Confirmado: fase actual es planificación, no desarrollo

### Decisiones tomadas en esta sesión
- Sistema de perfilamiento: CRM Espiritual con campos de carta natal, estado emocional, nivel de confianza (1-5), temas recurrentes, notas intuitivas, historial de sesiones
- Stack: aún no definido, en planificación
- Infraestructura: Hetzner servidor dedicado

---

## 2026-04-04 — Sesión 2: Expansión del modelo de negocio

- [x] Canales: WhatsApp, Instagram, Facebook (Meta unificado), TikTok
- [x] Conocimiento RAG: Tarot, Astrología, Numerología, Baraja española, Adivinación
- [x] Fuente RAG: libros y documentos propios del usuario
- [x] Modelo de negocio freemium: gratis → pago único → suscripción mensual
- [x] Stripe como pasarela (pagos únicos + suscripciones)
- [x] Agente Follower: mensajes diarios para suscriptores
- [x] Agente Monitor: análisis de conversaciones, gaps y oportunidades
- [x] E-commerce + herbolario/Flores de Bach: en evaluación

---

## 2026-04-04 — Sesión 3: Stack de embeddings y LLM definidos

- [x] Gemini Embedding 2 Preview (multimodal: texto 8192 tokens, audio 80s, vídeo 120s, PDF 6 pág.)
- [x] Qdrant como base vectorial (colección `esoter_knowledge`, cosine, 1536 dims MRL)
- [x] Estrategia LLM híbrida:
  - Claude → perfilado inicial + primera lectura (conversión)
  - DeepSeek V3 / Kimi K2 → lecturas post-perfil, análisis Monitor
  - DeepSeek / Kimi K2 → Follower diario + contenido redes (volumen bajo coste)
- [x] Orquestador confirmado: n8n + CrewAI (n8n = plomería/webhooks, CrewAI = agentes autónomos)

---

## 2026-04-04 — Sesión 4: Infraestructura servidor Hetzner

### Completado
- [x] Servidor Ubuntu 22.04 LTS en Hetzner (IP: 95.217.217.222)
- [x] Dominio `ether.care` configurado en Cloudflare
- [x] Subdominios activos: `n8n.`, `api.`, `admin.`, `system.`
- [x] SSL: Cloudflare Origin Certificate wildcard `*.ether.care` (15 años, sin renovación)
- [x] Nginx con SSL configurado y corriendo
- [x] Docker Compose con 6 servicios: postgres, qdrant, redis, n8n, crewai, nginx
- [x] PostgreSQL 16 con schema completo (14 tablas)
- [x] Redis 7 operativo
- [x] n8n operativo en `https://n8n.ether.care`
- [x] Credenciales todas generadas con regla de password (incluyen `X4pHUrxAFahF`)

### Problemas resueltos
- n8n EACCES /home/node/.n8n → `chown -R 1000:1000`
- nginx "host not found upstream crewai" → deshabilitar confs hasta tener imagen
- Qdrant healthcheck 401 → `docker-compose.override.yml` con `bash /dev/tcp`
- `$` en passwords del `.env` → escape como `$$`

---

## 2026-04-04 — Sesión 5: Pipeline RAG completo

### Completado
- [x] **CrewAI container** construido y corriendo (`https://api.ether.care`)
- [x] **Google API Key** configurada en `.env` (Gemini Embedding 2 Preview)
- [x] **DeepSeek API Key** configurada (sk-8a4694...)
- [x] **Pipeline RAG completo** implementado y operativo:
  - Chunkers: text/docx, PDF (5 pág/chunk), audio (70s/chunk), vídeo (100s/chunk)
  - Embeddings: Gemini Embedding 2 Preview con task prefixes
  - Clasificador motivacional: DeepSeek V3 (JSON structured output, confidence ≥ 0.65)
  - Qdrant store: colección `esoter_knowledge` creada automáticamente al arrancar
  - PostgreSQL: `knowledge_documents` + `knowledge_chunks_motivational` + anti-repeat log
  - API FastAPI: `POST /rag/ingest`, `POST /rag/search`, `GET /rag/documents`
- [x] **Schema PostgreSQL** aplicado (14 tablas + triggers `set_updated_at`)
- [x] **Fix QdrantClient**: añadido `https=False` para red interna Docker sin TLS

### Endpoints operativos
- `GET  https://api.ether.care/health` → `{"status":"ok","service":"esotersystem-api"}`
- `POST https://api.ether.care/rag/ingest` → ingesta multipart
- `POST https://api.ether.care/rag/search` → búsqueda semántica
- `GET  https://api.ether.care/rag/documents` → listado documentos indexados

---

## 2026-04-04 — Sesión 6: Flujos n8n RAG

### Completado
- [x] **Flujo 1 — RAG Ingesta** (ID: `3hl1d6HmMArnxFcu`):
  - Webhook `POST https://n8n.ether.care/webhook/rag-ingest`
  - Acepta multipart: `file` + `title` + `esoteric_system` + `description` + `author` + `tags`
  - Reenvía a `http://crewai:8000/rag/ingest` y devuelve respuesta JSON
- [x] **Flujo 2 — Chat RAG** (ID: `SBIKA7MHgz8C8fUA`):
  - Chat UI pública en `https://n8n.ether.care/webhook/rag-chat/chat`
  - Flujo: Chat → `/rag/search` Qdrant (top 5, score ≥ 0.45) → Code (formatea contexto) → DeepSeek V3 → respuesta
- [x] **Credencial DeepSeek** creada en n8n (ID: `PKoyLixZu1ip5CpT`, httpHeaderAuth)
- [x] **Fix n8n trust proxy**: añadidos `N8N_PROXY_HOPS: 1`, `N8N_EDITOR_BASE_URL`, `EXECUTIONS_PROCESS: main`, `N8N_PUSH_BACKEND: sse`

### URLs de uso
| Función | URL |
|---|---|
| Chat RAG (UI) | `https://n8n.ether.care/webhook/rag-chat/chat` |
| Ingesta docs (API) | `POST https://n8n.ether.care/webhook/rag-ingest` |
| API directa | `https://api.ether.care` |
| Panel n8n | `https://n8n.ether.care` |

---

## Sesión 7 — Flujos n8n finalizados y activados

### Completado
- [x] **Flujo 1 — Ingesta RAG** (ID: `D9i5LtrVSEx5Ye4P`) — ✅ ACTIVO
  - Form trigger: `https://n8n.ether.care/webhook/f1bb7a4e-2c91-4bad-89f4-e05759216ca0/form`
  - Campos: Archivo, Título, Sistema Esotérico (dropdown), Descripción, Autor, Tags
  - Reenvía multipart a `http://crewai:8000/rag/ingest`
- [x] **Flujo 2 — Chat RAG** (ID: `prju8dIHoMqSDGrv`) — ✅ ACTIVO
  - Chat UI pública en `https://n8n.ether.care/webhook/chat-rag-esoter-001/chat`
  - Pipeline: Chat Trigger → RAG Search (crewai:8000) → Code (formatear contexto) → DeepSeek V3 → Set output
  - DeepSeek usa credencial `PKoyLixZu1ip5CpT`
- [x] Nota: `validate_workflow` del MCP SDK roto (error interno); flujos creados via REST API directa

---

## Estado Actual de la Infraestructura

| Servicio | Estado | URL |
|---|---|---|---|
| PostgreSQL 16 | ✅ healthy | interno |
| Qdrant (vector DB) | ✅ healthy | interno |
| MySQL 8.0 (diagnóstico) | ✅ healthy | interno |
| Redis 7 | ✅ healthy | interno |
| CrewAI API | ✅ running | https://api.ether.care |
| n8n | ✅ running | https://n8n.ether.care |
| nginx | ✅ running | proxy SSL |
| LiveKit Server | ✅ running | ws://95.217.217.222:7880 |
| LiveKit Agent | ✅ registered | "esoter-therapist" |
| speaches (STT) | ✅ running | http://whisper:8000/v1 (int) / :8080 (ext) |
| MinIO | ✅ healthy | interno |
| Flujo Ingesta RAG | ✅ activo | Form webhook |
| Flujo Chat RAG | ✅ activo | Chat webhook |
| Flujo Tarot Significados | ✅ activo | interno |

---

## 2026-04-05 — Sesión 8: Schema Tarot + Subagente de Lectura

### Completado
- [x] **Schema `tarot` en PostgreSQL** — 6 tablas dentro de `esotersystem` DB:
  - `tarot_cards` — 78 cartas completas (mayor + menor)
  - `card_meanings` — significados por carta/posición (upright/reversed)
  - `tarot_spreads` — 8 tiradas activas (simple, relationship, career, decision, celtic)
  - `reading_sessions` — sesiones de lectura por usuario
  - `session_cards` — cartas lanzadas en cada sesión
  - `reading_interpretations` — interpretaciones LLM guardadas
- [x] **Flujo n8n "Tarot - Generador de Significados"** (ID: `CIEEiPv0UwQPRI9U`) — ACTIVO
  - Loop por cada carta sin significado → RAG search → DeepSeek V3 → INSERT en DB
  - Genera los 76 significados faltantes uno a uno con contexto RAG
- [x] **Subagente Tarot en CrewAI** — módulo `/crewai/src/tarot/` operativo:
  - `db.py` — operaciones asyncpg (draw_cards, get_card_meanings, create_reading_session, etc.)
  - `reader.py` — detect_area(), prepare_reading() (detecta área, elige tirada, extrae cartas)
  - `interpreter.py` — generate_reading() via DeepSeek V3, retorna JSON estructurado
  - `router.py` — endpoints FastAPI registrados en main.py
- [x] **Fix trigger PostgreSQL** — `tarot.complete_session_after_cards()` corregido con schema prefix

### Endpoints operativos (subagente tarot)
| Endpoint | Descripción |
|---|---|
| `POST https://api.ether.care/tarot/reading` | Lectura completa: cartas + interpretación + memory_summary |
| `GET  https://api.ether.care/tarot/spreads` | Tiradas disponibles |
| `GET  https://api.ether.care/tarot/session/{uuid}` | Recuperar sesión por UUID |
| `GET  https://api.ether.care/tarot/history/{user_id}` | Historial de lecturas de un usuario |

### Payload POST /tarot/reading
```json
{
  "question": "¿Cómo está mi situación de pareja?",
  "user_id": "wa:5491112345678",   // opcional, formato canal:id
  "area": "amor",                  // opcional, se auto-detecta
  "spread_type": "relationship"    // opcional, se auto-selecciona
}
```
### Response incluye
- `session_uuid` — ID único de la sesión (para recuperarla)
- `cards_drawn` — cartas extraídas con posición y keywords
- `overall_reading` — narrativa completa 3-4 párrafos
- `card_analysis` — interpretación carta por carta
- `advice` — consejo práctico
- `energy_summary` — frase poética resumen energético
- `memory_summary` — resumen de 120 palabras para memoria temporal del agente

### Problemas resueltos en esta sesión
- Schema `positions` en `tarot_spreads` es JSON array, no dict → fix en reader.py
- Trigger `complete_session_after_cards` sin schema prefix → `CREATE OR REPLACE FUNCTION tarot.complete_session_after_cards()`
- Columnas reales difieren del plan inicial: `card_count` vs `num_cards`, `area_of_life` vs `consultation_area`, etc.
- MySQL descartado, todo en PostgreSQL (schema `tarot`)

---

## 2026-04-06 — Sesión 9: Agente Telegram conversacional + Memoria Redis + RAG

### Completado
- [x] **Agente Telegram v1** (ID: `iZwvyZQuNOD9y9SZ`) — simple clasificar→responder (desactivado)
- [x] **Agente Telegram v2** (ID: `8I6Fzzrq18fE6XXm`) — ACTIVO con:
  - Memoria Redis por usuario (TTL 30 días, clave `user:tg:{id}`)
  - Orquestador DeepSeek: decide acción conversacional (respond/ask_area/do_reading/follow_up)
  - RAG search antes de cada lectura de tarot (contexto esotérico)
  - `rag_context` inyectado en el prompt del subagente tarot
  - 16 nodos: Telegram Trigger → Normalizar → Redis GET → Armar Contexto → DeepSeek Orquestador → Parsear Decision → IF → [tarot: RAG→Tarot→Formatear→Redis SET→Send] / [general: Prep→Redis SET→Send]
- [x] **Bot Telegram**: @tutarot_bot (`t.me/tutarot_bot`)
- [x] **crewai /tarot/reading**: acepta `rag_context` opcional, lo inyecta en el prompt de DeepSeek
- [x] **Redis credential**: ID `rtEuHt9JGAuusga0`, host `redis`, password `hN6` (real password truncada por bug shell en .env)
- [x] **Fix docker-compose.yml**: Redis command usa JSON array para evitar interpretación de `&` en password

### Bug encontrado y corregido
- `REDIS_PASSWORD=hN6&X4pHUrxAFahFcY4^dM1q` en `.env` → el `&` hacía que docker-compose pase solo `hN6` como password a Redis
- Fix: `command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}", ...]` (JSON array, sin shell)
- La password real de Redis en producción es `hN6` hasta próximo restart del container

### TODO urgente post-restart Redis
- Al reiniciar Redis, el password será el de .env completo (`hN6&X4pHUrxAFahFcY4^dM1q`)
- Actualizar credential n8n Redis con el password correcto
- O cambiar REDIS_PASSWORD en .env a un password sin caracteres especiales de shell

---

---

## 2026-04-25 — Sesión 10: STT local con LiveKit + speaches

### Completado
- [x] **STT migrado de Deepgram (pago) → self-hosted gratuito**:
  - Deepgram → whisper.cpp (no soporta Opus/Ogg) → speaches (faster-whisper, soporta Opus/Ogg/WAV/MP3)
- [x] **speaches configurado y corriendo** (`ghcr.io/speaches-ai/speaches:latest-cpu`)
  - Modelo: `Systran/faster-whisper-small` (~1 GB RAM)
  - Cache persistente en volumen Docker (`/home/ubuntu/.cache/huggingface`)
  - Puerto: `8080` externo → `8000` interno
  - Healthcheck configurado (start_period: 120s)
  - API OpenAI-compatible verificada: `POST /v1/audio/transcriptions` → `{"text":""}` ✅
- [x] **LiveKit agent configurado** para usar speaches como STT:
  - `openai.STT(model="Systran/faster-whisper-small", base_url="http://whisper:8000/v1", language="es")`
- [x] **Docker Compose** actualizado:
  - Bloque `whisper` con variables correctas (`WHISPER__MODEL`, `WHISPER__COMPUTE_TYPE`, etc.)
  - `livekit-agent` con `WHISPER_URL=http://whisper:8000/v1`
- [x] **Contenedor estable** (sin OOM — 3.7 GiB RAM total en servidor)

### Problemas resueltos
- `ASR_MODEL: large-v3-turbo` no es válido para speaches → usa `WHISPER__MODEL: Systran/faster-whisper-small`
- `WHISPER_PORT` no es variable de speaches → quitada
- Puerto mapeado `8080:8080` cuando speaches escucha en `8000` → corregido a `8080:8000`
- Cache path incorrecto `/root/.cache/whisper` → `/home/ubuntu/.cache/huggingface`
- `deepdml/faster-whisper-large-v3-turbo-ct2` causaba OOM (~3 GB) → bajado a `Systran/faster-whisper-small` (~1 GB)

### Decisiones tomadas
- Modelo pequeño pero estable para STT; si se necesita más precisión, ampliar RAM del servidor o añadir swap
- `livekit-agent` y `whisper` en misma red Docker (`esoter_net`) → comunicación por nombre de servicio, no por host IP

---

## Pendiente — Próximas Sesiones

### Prioridad Alta
1. [ ] **Probar LiveKit + STT end-to-end** — conectar cliente LiveKit, hablar, verificar transcripción
2. [ ] **Crear workflow n8n "WF_Diagnostico"** — 16 nodos, diagnóstico psicológico en 10 pasos
3. [ ] Probar agente Telegram v2 (@tutarot_bot) — conversación + memoria + tarot
4. [ ] Limpiar REDIS_PASSWORD en .env (sin `&`, `^`, etc.) y reiniciar Redis
5. [ ] Configurar Meta Webhook (WhatsApp + Instagram + Facebook)
6. [ ] Conseguir Claude API key (para perfilado inicial)

### Prioridad Media
7. [ ] Conseguir Kimi K2 API key
8. [ ] Configurar Stripe (clave secreta + webhook secret)
9. [ ] Definir precio lectura de pago y plan mensual
10. [ ] Flujo n8n: Stripe webhook → activar suscripción en DB
11. [ ] Subir primeros documentos al RAG (libros de tarot)

### Prioridad Baja
12. [ ] Diseño panel admin CRM (admin.ether.care)
13. [ ] Agente Follower (mensajes diarios motivacionales)
14. [ ] Agente Monitor (inteligencia de negocio)
15. [ ] Integración TikTok
16. [ ] Análisis viabilidad herbolario / Flores de Bach

---

## Plan: Flujo n8n — Agente de Relaciones con Clientes

### Objetivo
Flujo n8n que recibe mensajes de WhatsApp/Instagram/Facebook, gestiona la conversación
y llama al subagente de Tarot cuando el usuario lo solicita.

### Arquitectura del flujo

```
[Webhook Meta / WhatsApp]
        ↓
[Normalize Message]  — extrae user_id, canal, texto
        ↓
[Redis: Cargar Memoria]  — GET session:{user_id} (contexto últimos N mensajes)
        ↓
[DeepSeek: Clasificar Intención]
  - "saludo" → respuesta bienvenida
  - "tarot" → llamar subagente tarot
  - "pregunta_general" → buscar RAG + responder
  - "pago" → info Stripe
  - "otro" → respuesta genérica
        ↓ (si intención = "tarot")
[POST http://crewai:8000/tarot/reading]
  body: {question, user_id, area}
        ↓
[Formatear Lectura]  — texto legible para WhatsApp (sin markdown complejo)
        ↓
[Redis: Guardar Memoria]  — SET session:{user_id} con memory_summary + historial
        ↓
[Enviar Respuesta]  — WhatsApp/Meta API
```

### Nodos n8n necesarios (estimado: 10-12 nodos)
1. **Webhook** — recibe POST de Meta
2. **Code: Normalize** — extrae canal, user_id, mensaje_texto
3. **HTTP: Redis GET** — carga contexto de sesión
4. **HTTP: DeepSeek classify** — clasifica intención (JSON: {intent, area, confidence})
5. **Switch** — ramifica por intent
6. **HTTP: POST /tarot/reading** — llama subagente (rama tarot)
7. **HTTP: POST /rag/search** — busca contexto (rama pregunta_general)
8. **HTTP: DeepSeek respond** — genera respuesta final con contexto
9. **Code: Format** — adapta respuesta a formato WhatsApp
10. **HTTP: Redis SET** — guarda memoria de sesión (TTL 24h)
11. **HTTP: Meta Send** — envía mensaje de vuelta

### Memoria de sesión (Redis)
```json
{
  "user_id": "wa:5491112345678",
  "last_active": "2026-04-05T16:00:00Z",
  "messages": [...últimos 5 mensajes...],
  "last_reading": {
    "session_uuid": "eb40ff06-...",
    "memory_summary": "Área: Amor. Cartas: El Carro..."
  },
  "profile": {
    "name": "María",
    "tone": "empático"
  }
}
```

### user_id format
- WhatsApp: `wa:{phone}` (ej. `wa:5491112345678`)
- Instagram: `ig:{ig_user_id}`
- Facebook: `fb:{psid}`
