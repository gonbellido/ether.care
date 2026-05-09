# Hallazgos — Kokoro TTS + Edge TTS + STT

## Estado del despliegue (final)

| Componente | Backend | Status | Detalle |
|-----------|---------|--------|---------|
| `GET /health` | — | ✅ 200 | `{"status":"ok"}` |
| `GET /voices` | — | ✅ 200 | 16 voces (11 EN + 5 ES) |
| `POST /tts` (en inglés) | Kokoro | ✅ 200 | WAV ~200KB por frase corta |
| `POST /tts` (español) | Edge TTS | ✅ 200 | MP3 ~25KB / WAV ~137KB |
| `POST /stt` | faster-whisper | ✅ 200 | Transcribe silencio correctamente |

## Problemas encontrados y soluciones

### 1. Voces españolas de Kokoro no disponibles (fixed)
Kokoro-82M lista `es_mercedes` y `es_juan` en su documentación pero los `.pt`
no existen en HuggingFace. Cualquier intento de usarlas daba 500.

**Solución:** Se eliminaron del diccionario `VOICES` y se implementó Edge TTS
(Microsoft) como backend para español. Edge TTS es gratuito, no requiere API key,
y ofrece voces neurales de alta calidad.

### 2. python-multipart faltante (fixed v2)
FastAPI requiere `python-multipart` para `Form()` y `UploadFile`. Se añadió al
`Dockerfile`.

### 3. run_in_executor con keyword arguments (fixed v3)
`loop.run_in_executor()` no acepta `**kwargs`. La función `_kokoro_tts` fallaba
con `TypeError: unexpected keyword argument 'voice'`.

**Solución:** Usar `lambda: tts(text, voice=voice_id, speed=speed)` en lugar de
pasar kwargs directamente.

### 4. Llamada a edge-tts con HTTP en lugar de HTTPS
Edge TTS usa la API de Microsoft Cognitive Services. Todo funciona sin API key.

### 5. Docker cache issues durante rebuild
Docker compose bake cachea las capas. Los SCP de archivos actualizados no siempre
invalidan la caché porque la build context se carga al inicio. Tras varios
rebuilds: la causa raíz fue que el container no se recreó desde la nueva imagen
(`docker compose up -d` decía "Recreate" pero usaba la imagen vieja).

**Solución:** Forzar `docker rm` + `docker rmi` antes de rebuild.

### 6. Disk space en Hetzner
38GB de disco, ~28GB usados. Las imágenes Docker con Kokoro + faster-whisper +
PyTorch (CUDA) pesan ~3.2GB. La build cache acumuló 13GB. Errores de "no space
left on device" durante builds con `--no-cache`.

**Solución:** `docker builder prune` y eliminar imágenes intermedias no usadas.

## Análisis de seguridad

| Aspecto | Estado | Riesgo |
|---------|--------|--------|
| Exposición a internet | ✅ No expuesto (sin `ports:` en compose) | Bajo |
| Autenticación | ❌ No tiene | Medio (solo red interna) |
| Rate limiting | ❌ No tiene | Bajo |
| Límite tamaño STT | ❌ No tiene | Medio (posible fill disk) |
| Limpieza temp files | ✅ finally block | Bajo |
| HTTPS | ✅ No aplica (interno) | Bajo |

**Conclusión:** El servicio está bien aislado en la red interna Docker. Solo
servicios controlados (n8n, crewai) tienen acceso. Riesgos aceptables para el
contexto actual.

## Recomendaciones futuras
1. Añadir límite de tamaño en `POST /stt` (10MB max)
2. Añadir límite de caracteres en `POST /tts` (2000 chars max)
3. Si se expone a internet: API Key + rate limit + HTTPS vía nginx
4. Evaluar Piper TTS como alternativa local a Edge TTS para español

## Revisión General y Correcciones de Integración (Jules - 2026-04-04)

### 1. Corrección de Puertos y Conectividad
- Se detectó que `livekit-agent` intentaba conectar a Whisper en el puerto 8080, el cual es el puerto externo. Se corrigió al puerto 8000 para comunicación interna entre contenedores Docker.
- Se sincronizaron las dimensiones de embeddings a 3072 (Full) en todo el proyecto, corrigiendo discrepancias entre el código (config.py) y la documentación/setup de Qdrant.

### 2. Implementación de Journey Management
- Se implementó el `JourneyManager` en `crewai/src/agents/journey_manager.py` para gestionar el estado de las sesiones en la base de datos MySQL `diagnostico`.
- Se añadieron endpoints a la API de CrewAI (`/journey/{session_id}` y `/journey/update`) para permitir que n8n u otros servicios consulten y actualicen el progreso del usuario en los 10 pasos terapéuticos.

### 3. Reducción de Latencia Percibida (Animator)
- Se incorporó la lógica del "Agente de Interfaz" (Animador) directamente en el `livekit-agent`. Ahora, el sistema emite frases de relleno ("Entiendo...", "Déjame ver...") mientras espera la respuesta pesada de n8n/RAG, mejorando significativamente la experiencia de usuario en voz.

### 4. Estructuración de Agentes CrewAI
- Se crearon las clases base y específicas para los agentes principales (`ProfilerAgent`, `AdvisorAgent`, `KnowledgeCuratorAgent`) en el directorio `crewai/src/agents/`, siguiendo las especificaciones de `agents.md`.

### 5. Dependencias
- Se añadió `aiomysql` a `crewai/requirements.txt` para soportar la conexión asíncrona con la base de datos de diagnóstico.
