# Specification: EsoterSystem — Sistema Multi-Agente Autónomo

**Issue**: esotersystem-v1
**Status**: en refinamiento

## Overview

EsoterSystem es una plataforma de agentes autónomos que trabajan de forma coordinada para:
1. Gestionar múltiples canales de comunicación (WhatsApp, Instagram, Facebook, TikTok)
2. Construir y mantener un **CRM espiritual** de cada persona (perfil energético + historial de sesiones)
3. Ofrecer asesoramiento personalizado (tarot, astrología, numerología, baraja española, adivinación)
4. **Monetizar** el servicio mediante lecturas de pago (Stripe) y planes de seguimiento mensuales
5. **Hacer seguimiento activo** de cada cliente con mensajes diarios personalizados
6. **Analizar el negocio** de forma continua para detectar mejoras, gaps de conocimiento y oportunidades

El sistema actúa como un consultor espiritual inteligente omnicanal con modelo freemium: primera lectura gratuita como captación, lecturas completas de pago, y planes de seguimiento mensual como recurrencia.

---

## Modelo de Negocio

### Flujo de conversión
```
[Lead entra por cualquier canal]
        ↓
[Lectura gratuita inicial] ← Agente Asesor (básica, sin cobro)
        ↓
[Oferta de lectura completa] ← Enlace Stripe (pago único, precio económico)
        ↓
[Pago confirmado] → [Lectura completa personalizada]
        ↓
[Oferta plan mensual de seguimiento]
        ↓
[Suscripción activa] → [Mensajes diarios de seguimiento por agente]
```

### Planes y productos
| Producto | Tipo | Canal de pago |
|---------|------|--------------|
| Lectura inicial | Gratis | — |
| Lectura completa | Pago único | Stripe (link) |
| Plan mensual de seguimiento | Suscripción | Stripe Subscriptions |
| (Futuro) Productos físicos / herbolario | E-commerce | Stripe / tienda online |

---

## Catálogo de Agentes

| Agente | Rol |
|--------|-----|
| **Orchestrator** | Coordinador central — enruta mensajes al agente correcto según contexto y estado del cliente |
| **Profiler** | Extrae datos del cliente de las conversaciones y enriquece el CRM |
| **Advisor** | Genera lecturas y asesoramiento usando perfil + RAG de conocimiento esotérico |
| **Follower** | Envía mensajes diarios de seguimiento a suscriptores (objetivos, desafíos, afirmaciones) |
| **Monitor** | Analiza conversaciones para detectar mejoras, gaps de conocimiento y oportunidades de negocio |
| **Payment Gateway** | Gestiona el flujo de pago con Stripe (genera links, verifica pagos, activa servicios) |
| **Channel Adapters** | Normalizan mensajes de cada canal al formato interno del sistema |

---

## Modelo de Datos — CRM Espiritual

### Entidad: Cliente
| Campo | Tipo | Descripción |
|-------|------|-------------|
| nombre | string | Nombre completo |
| fecha_nacimiento | date | Para carta natal y numerología |
| signo / carta_natal | string/json | Signo solar, ascendente, etc. |
| estado_emocional_actual | string | Estado en el momento actual |
| nivel_confianza | int (1–5) | Apertura al trabajo espiritual |
| temas_recurrentes | array | amor, dinero, familia, trabajo, salud |
| ultima_sesion | date | Fecha de la última consulta |
| canales | array | IDs por canal (WA, IG, FB, TT) |
| notas_intuitivas | text | Notas del consultor |
| relaciones | refs | Vínculos con otros clientes |
| plan_activo | enum | free, lectura_pago, mensual |
| stripe_customer_id | string | ID del cliente en Stripe |
| suscripcion_activa | bool | Si tiene plan mensual vigente |
| objetivos_actuales | array | Objetivos declarados del cliente |
| desafios_actuales | array | Desafíos identificados |

### Entidad: Sesión
| Campo | Tipo | Descripción |
|-------|------|-------------|
| cliente | ref | Referencia al cliente |
| fecha | datetime | Cuándo fue la sesión |
| tipo | enum | tarot, astrología, numerología, baraja_española, adivinación |
| es_gratuita | bool | Si fue la lectura gratis de captación |
| pregunta_principal | text | Lo que el cliente quería saber |
| cartas_tiradas | array | Si aplica |
| interpretacion | text | Lo que se leyó / canalizó |
| energia_percibida | text | Notas de energía |
| proximos_pasos | text | Actividades o seguimiento |
| stripe_payment_id | string | ID del pago si fue sesión de pago |

### Entidad: Mensaje de Seguimiento
| Campo | Tipo | Descripción |
|-------|------|-------------|
| cliente | ref | Destinatario |
| fecha_envio | datetime | Cuándo se envió |
| canal | enum | whatsapp, instagram, etc. |
| tipo | enum | objetivo, desafio, afirmacion, recordatorio |
| contenido | text | El mensaje enviado |
| estado | enum | pendiente, enviado, leido |

### Entidad: Observación de Monitor
| Campo | Tipo | Descripción |
|-------|------|-------------|
| fecha | datetime | Cuándo se detectó |
| tipo | enum | gap_conocimiento, solicitud_nueva, mejora_respuesta, oportunidad_negocio |
| descripcion | text | Qué se detectó |
| conversacion_ref | ref | Conversación de origen |
| prioridad | enum | alta, media, baja |
| estado | enum | nueva, en_revision, resuelta |

---

## Requirements

### Must Have
- [ ] Agente Orquestador central
- [ ] Integración WhatsApp (Meta Cloud API)
- [ ] Integración Instagram + Facebook (Meta Webhook unificado)
- [ ] Agente Perfilador: enriquece CRM desde conversaciones
- [ ] CRM espiritual persistente
- [ ] Agente Asesor con RAG (tarot, astrología, numerología, baraja española, adivinación)
- [ ] Flujo freemium: lectura gratis → oferta de pago → Stripe link → lectura completa
- [ ] Integración Stripe (pagos únicos + suscripciones)
- [ ] Agente Follower: mensajes diarios para suscriptores
- [ ] Agente Monitor: analiza conversaciones y genera observaciones
- [ ] Acceso al perfil completo en < 10 segundos (panel CRM)

### Should Have
- [ ] Integración TikTok DM
- [ ] Panel de administración web (CRM + observaciones del Monitor)
- [ ] Vinculación de perfiles multi-canal
- [ ] Agente de análisis de sentimiento y estado emocional
- [ ] Exportación de perfiles y reportes
- [ ] Dashboard de métricas de negocio (conversiones, ingresos, gaps)

### Para Evaluar / Futuro
- [ ] E-commerce de productos físicos (libros, complementos de terapias alternativas)
- [ ] Herbolario online (Flores de Bach + productos de herboristería)
- [ ] App móvil propia

### Won't Have (por ahora)
- Videollamadas
- Integración con ERPs o contabilidad

---

## Acceptance Criteria

- [ ] Mensaje entrante → respuesta personalizada en < 10 segundos
- [ ] Perfil del cliente se actualiza automáticamente tras cada interacción
- [ ] Sistema identifica al mismo cliente en diferentes canales
- [ ] Base de conocimiento actualizable sin redeploy
- [ ] Flujo de pago completo: link Stripe → webhook confirmación → activación del servicio
- [ ] Suscriptor recibe al menos 1 mensaje diario de seguimiento
- [ ] Monitor genera al menos 1 observación por sesión analizada
- [ ] Panel CRM muestra perfil completo en < 10 segundos

---

## User Stories

Como **lead nuevo** que escribe por WhatsApp, quiero recibir una lectura gratuita y luego tener la opción de pagar por una más completa de forma fácil.

Como **cliente de pago**, quiero recibir una lectura completa y personalizada que refleje mi perfil y mi situación actual.

Como **suscriptor mensual**, quiero recibir mensajes diarios que me ayuden a mantenerme enfocado en mis objetivos y desafíos espirituales.

Como **consultor/admin**, quiero ver en el panel CRM todo el historial del cliente en 10 segundos antes de una sesión.

Como **Monitor**, quiero analizar las conversaciones y reportar: qué preguntas no supe responder, qué solicitan los clientes que no ofrecemos, y qué oportunidades de negocio hay.

---

## Edge Cases

| Case | Handling |
|------|----------|
| Cliente nuevo sin perfil | Crear perfil base, flujo de bienvenida + lectura gratuita |
| Pago fallido o no completado | Notificar al cliente, no activar servicio, reintentar con nuevo link |
| Suscripción cancelada | Desactivar Follower, conservar historial, ofrecer reactivación |
| Monitor detecta gap crítico | Crear observación de prioridad alta, notificar al admin |
| Cliente solicita algo fuera del catálogo | Monitor lo registra, Asesor da respuesta empática + redirige |
| Mensaje de alta carga emocional/crisis | Protocolo de contención: empatía primero, seguimiento humano |
| Consultor añade nota intuitiva | Comando /nota → guarda en perfil sin responder al cliente |
