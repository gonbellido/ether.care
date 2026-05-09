# EsoterSystem

Sistema multi-agente autónomo para gestión omnicanal, perfilamiento de personas y asesoramiento personalizado.

## Qué hace

- **Gestión de canales**: Recibe y responde mensajes de WhatsApp, redes sociales y otros canales desde un único sistema
- **Perfilamiento**: Construye automáticamente un perfil de cada persona basado en sus interacciones
- **Asesoramiento**: Genera respuestas y actividades personalizadas usando una base de conocimiento especializada
- **Memoria**: Recuerda el historial y contexto de cada persona en todos los canales

## Agentes

| Agente | Rol |
|--------|-----|
| **Orchestrator** | Coordinador central — decide qué agentes activar por cada mensaje |
| **Profiler** | Extrae información del usuario y actualiza su perfil |
| **Advisor** | Genera respuestas, consejos y actividades basadas en perfil + conocimiento |
| **Channel Adapters** | Normalizan mensajes de cada canal al formato interno |

## Estado

🟡 En definición — pendiente de especificar sistema de perfilamiento y base de conocimiento.

## Documentación

- [Especificación](.project/esotersystem/spec.md)
- [Plan de implementación](.project/esotersystem/plan.md)
- [Investigación y decisiones](.project/esotersystem/findings.md)
- [Progreso](.project/esotersystem/progress.md)
