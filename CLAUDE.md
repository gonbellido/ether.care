# EsoterSystem — CLAUDE.md

## Descripción del Proyecto

Sistema multi-agente autónomo para gestión omnicanal (WhatsApp, redes sociales), perfilamiento de usuarios y asesoramiento personalizado basado en base de conocimiento.

## Arquitectura de Agentes

```
[WhatsApp / Redes Sociales]
        ↓
[Channel Adapters]  — normalizan mensajes al formato interno
        ↓
[Orchestrator Agent]  — decide qué agentes activar
    ↙        ↘
[Profiler]   [Advisor]
    ↓            ↓
[Profiles DB] [Knowledge Base]
        ↘    ↙
      [Response] → [Canal de origen]
```

## Estructura de Directorios

```
esotersystem/
├── agents/
│   ├── orchestrator/   # Agente coordinador central
│   ├── profiler/       # Agente de perfilamiento de usuarios
│   ├── advisor/        # Agente asesor (respuestas + actividades)
│   └── channels/       # Agentes específicos de canal
├── channels/
│   ├── whatsapp/       # Integración WhatsApp Business API
│   └── social/         # Integración redes sociales
├── knowledge_base/     # Base de conocimiento esotérico/especializado
├── profiles/           # Esquemas y gestión de perfiles de usuario
├── config/             # Configuración del sistema
├── livekit-agent/      # Agente LiveKit (STT → n8n → TTS)
├── livekit/            # Config LiveKit server
├── whisper/            # (legacy — reemplazado por speaches)
├── nginx/              # Config reverse proxy + SSL
├── postgres/           # Init scripts PostgreSQL
├── mysql/              # Init scripts MySQL (diagnóstico)
├── crewai/             # Subagentes autónomos (tarot, RAG, etc.)
├── qdrant/             # Datos vectoriales
├── redis/              # Datos Redis
├── minio/              # Datos documentales
└── .project/           # Archivos de gestión del proyecto
    ├── esotersystem/
    │   ├── spec.md
    │   ├── plan.md
    │   ├── findings.md
    │   └── progress.md
    └── diagnostico-psicologico/
        └── spec.md
```

## Estado Actual

**Fase**: Implementación — Infraestructura STT completa

### Servicios en Producción
| Servicio | Estado | Puerto |
|---|---|---|
| PostgreSQL 16 | ✅ | interno |
| Qdrant | ✅ | 6333-6334 |
| Redis 7 | ✅ | 6379 |
| n8n | ✅ | 5678 (vía nginx SSL) |
| CrewAI API | ✅ | 8000-8001 (vía nginx SSL) |
| LiveKit Server | ✅ | 7880 (host mode) |
| LiveKit Agent | ✅ | conectado |
| speaches (STT) | ✅ | 8080 ext→8000 int |
| MinIO | ✅ | 9000-9001 |
| MySQL 8.0 | ✅ | 3306 |

### Stack Tecnológico
- **Orquestación**: n8n + CrewAI (n8n = webhooks/flujos, CrewAI = subagentes autónomos)
- **LLMs**: DeepSeek V3, Groq (Llama 3.3 70B), Anthropic Claude
- **Canales**: Telegram (@tutarot_bot), WhatsApp (pendiente Meta), próximamente Instagram/Facebook
- **RAG**: Qdrant + Gemini Embedding 2 + pipeline multimodal
- **Voice**: LiveKit (real-time voice bridge) + speaches (STT local) + Cartesia (TTS externo)
- **DB**: PostgreSQL (principal), MySQL (diagnóstico)
- **Documentos**: MinIO (wiki-raw + wiki-articles)
- **Cache/Colas**: Redis (memoria sesiones, cola tareas Agente Curador)

## Convenciones

- Cada agente vive en su propio directorio con su `README.md`
- Los mensajes entre agentes usan un schema JSON estándar (a definir en `config/message_schema.json`)
- Los perfiles de usuario se almacenan con un ID único por canal y un ID global unificado
- La base de conocimiento es actualizable sin redeployar el sistema
