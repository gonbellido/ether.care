# Plan: EsoterSystem — Sistema Multi-Agente Autónomo

**Issue**: esotersystem-v1
**Phase**: specify (refinando) → plan
**Started**: 2026-04-04

## Goal

Construir un sistema de agentes autónomos sobre un servidor Hetzner dedicado que:
1. Atiende clientes por WhatsApp y redes sociales
2. Mantiene un CRM Espiritual por cliente (perfil energético + historial de sesiones)
3. Genera respuestas y actividades personalizadas usando ese CRM + base de conocimiento esotérico

**El valor clave**: el consultor espiritual abre el perfil de un cliente y en 10 segundos sabe todo lo que necesita para la sesión.

## Approach (Preliminar — sujeto a revisión)

- **CRM Espiritual**: BD relacional PostgreSQL (Cliente + Sesión + Mensaje Seguimiento + Observación Monitor)
- **RAG Multimodal**: Gemini Embedding 2 → pgvector (mismo servidor) — texto, audio y vídeo
- **LLM Router (3 niveles)**:
  - Claude → perfilado inicial + primera lectura (calidad, empatía, conversión)
  - DeepSeek V3 / Kimi K2 → lecturas post-perfil, seguimientos, análisis del Monitor
  - DeepSeek / Kimi K2 → mensajes diarios Follower + generación de contenido en redes (volumen)
- **Canales**: Meta Webhook unificado (WA+IG+FB) + TikTok separado
- **Monetización**: Stripe (pagos únicos + suscripciones)
- **Seguimiento**: Agente Follower con scheduler diario
- **Inteligencia de negocio**: Agente Monitor (batch asíncrono)
- **Infraestructura**: Hetzner dedicado, todo Docker Compose

## Fases de Planificación (antes de desarrollo)

### Fase 0: Planificación Completa (ACTUAL)
- [x] 0.1: Definir canales → WhatsApp, Instagram, Facebook, TikTok
- [x] 0.2: Definir base de conocimiento → Tarot, Astrología, Numerología, Baraja española, Adivinación
- [x] 0.3: Confirmar fuente del conocimiento → libros y documentos propios del usuario (RAG)
- [x] 0.4: Definir modelo de datos CRM Espiritual (Cliente + Sesión)
- [x] 0.5: Definir motor de embeddings → Gemini Embedding 2 (multimodal)
- [x] 0.6: Definir estrategia LLM híbrida (Claude + DeepSeek/Kimi K2 según tarea)
- [x] 0.7: Confirmar orquestador de agentes → **n8n + CrewAI**
- [ ] 0.8: Diseñar esquema de base de datos detallado con relaciones
- [ ] 0.9: Diseñar protocolo de comunicación entre agentes (schema JSON + LLM router)
- [ ] 0.10: Diseñar arquitectura de infraestructura en Hetzner (Docker Compose + servicios)
- [ ] 0.11: Diseñar mockup / wireframe del panel de administración CRM
- [ ] 0.12: Decidir precio lectura de pago y plan mensual

## Fases de Implementación (post-planificación)

### Fase 1: Infraestructura Base
- [ ] 1.1: Montar servidor Hetzner + Docker Compose base
- [ ] 1.2: Implementar base de datos (PostgreSQL + pgvector en mismo servidor)
- [ ] 1.3: Implementar esquema CRM Espiritual completo
- [ ] 1.4: Implementar API interna (endpoints para agentes)
- [ ] 1.5: Implementar sistema de autenticación (admin + agentes)
- [ ] 1.6: Pipeline de ingesta RAG — **texto** (PDF/Word → chunks → Gemini Embedding 2 → pgvector)
- [ ] 1.7: Pipeline de ingesta RAG — **audio** (mp3/wav → transcripción → embedding → pgvector)
- [ ] 1.8: Pipeline de ingesta RAG — **vídeo** (mp4 → extracción audio+frames → embedding → pgvector)
- [ ] 1.9: Panel de carga de contenido al RAG (admin sube archivos, el pipeline los procesa)
- [ ] 1.10: Cargar base de conocimiento inicial (libros y documentos del usuario)

### Fase 2: Canal WhatsApp + Núcleo de Agentes
- [ ] 2.1: Implementar adaptador WhatsApp (Meta Cloud API)
- [ ] 2.2: Implementar Agente Orquestador
- [ ] 2.3: Implementar Agente Perfilador v1
- [ ] 2.4: Implementar Agente Asesor v1 (RAG esotérico)
- [ ] 2.5: Flujo freemium completo: bienvenida → lectura gratis → oferta de pago

### Fase 3: Monetización con Stripe
- [ ] 3.1: Integrar Stripe (pagos únicos — lectura completa)
- [ ] 3.2: Integrar Stripe Subscriptions (plan mensual)
- [ ] 3.3: Webhook Stripe → activación automática de servicio tras pago
- [ ] 3.4: Agente Payment Gateway (genera links, verifica estado)

### Fase 4: Agente Follower (Seguimiento Diario)
- [ ] 4.1: Implementar Agente Follower
- [ ] 4.2: Generación de mensajes diarios personalizados (objetivos + desafíos)
- [ ] 4.3: Scheduler de envíos (cron por cliente según zona horaria)
- [ ] 4.4: Flujo de activación/desactivación según estado de suscripción

### Fase 5: Agente Monitor + Panel de Admin
- [ ] 5.1: Implementar Agente Monitor (análisis asíncrono de conversaciones)
- [ ] 5.2: Sistema de observaciones (gaps, solicitudes, oportunidades)
- [ ] 5.3: Panel de administración CRM (perfiles, sesiones, historial)
- [ ] 5.4: Dashboard de Monitor (observaciones + métricas de negocio)

### Fase 6: Canales Adicionales
- [ ] 6.1: Adaptador Instagram + Facebook (Meta Webhook unificado)
- [ ] 6.2: Vinculación de perfiles multi-canal
- [ ] 6.3: Adaptador TikTok DM

### Fase 7: E-commerce (si se confirma)
- [ ] 7.1: Análisis de viabilidad herbolario / Flores de Bach
- [ ] 7.2: Decisión plataforma (tienda propia vs Shopify/WooCommerce)
- [ ] 7.3: Integración recomendación de productos desde Agente Asesor

## Current Step

**FASE 0 — Planificación**: Stack 100% definido. Próximo paso: esquema de BD + arquitectura Hetzner.

## Blockers

- Stack tecnológico: pendiente (post-planificación completa)
- Formato de documentos para el RAG: pendiente de confirmar

## Validation

- [ ] Perfil de cliente accesible en < 10 segundos con toda la información relevante
- [ ] Mensaje WhatsApp → respuesta personalizada en < 10s
- [ ] Perfil se actualiza automáticamente tras cada interacción
- [ ] Base de conocimiento actualizable sin redeploy
- [ ] Panel CRM muestra: nombre, signo, temas recurrentes, última sesión, notas
