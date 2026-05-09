# Kokoro (English) + Edge TTS (Spanish) + Faster-Whisper STT

Módulo de voz para EsoterSystem. Proporciona TTS y STT a través de una API HTTP
consumible desde n8n y otros servicios en la red interna Docker.

## Stack

| Componente  | Tecnología        | Modelo / Backend              | Idiomas                     |
|-------------|-------------------|-------------------------------|-----------------------------|
| TTS inglés  | Kokoro v0.7+      | Kokoro-82M (local / HF)       | Inglés (US / UK) — 11 voces |
| TTS español | Edge TTS          | Microsoft Neural (API gratuita, requiere internet) | Español (ES, MX, AR) — 5 voces |
| STT         | faster-whisper    | base (int8 CPU)               | Multilingüe                 |

## Endpoints

### `GET /health`
```json
{"status": "ok"}
```

### `GET /voices`
```json
{
  "voices": {
    "en_us_female_bella": "af_bella",
    "en_us_female_sarah": "af_sarah",
    ...
    "es_es_female_elvira": "es-ES-ElviraNeural",
    "es_es_male_alvaro": "es-ES-AlvaroNeural",
    "es_mx_female_dalia": "es-MX-DaliaNeural",
    "es_mx_male_jorge": "es-MX-JorgeNeural",
    "es_ar_female_elena": "es-AR-ElenaNeural"
  }
}
```

### `POST /tts`
Sintetiza texto a audio.

| Parámetro | Tipo   | Default        | Descripción                         |
|-----------|--------|----------------|-------------------------------------|
| `text`    | string | (obligatorio)  | Texto a sintetizar                  |
| `voice`   | string | `af_bella`     | Voz (ver /voices)                   |
| `speed`   | float  | 1.0            | Velocidad (0.5–2.0, solo Kokoro)    |
| `fmt`     | string | `wav`          | Formato: `wav`, `flac`, `ogg`, `mp3`|

- **Backend Kokoro** (voces `en_*`): formatos nativos WAV/FLAC/OGG; `mp3` se convierte vía ffmpeg.
- **Backend Edge** (voces `es_*`): formato nativo MP3; `wav`/`flac`/`ogg` se convierten vía ffmpeg.

**Respuesta:** archivo de audio con `Content-Type` según formato.

### `POST /stt`
Transcribe audio a texto.

| Parámetro  | Tipo        | Default | Descripción                        |
|------------|-------------|---------|------------------------------------|
| `file`     | UploadFile  | req     | Archivo de audio (wav, mp3, etc.)  |
| `language` | string      | auto    | Código ISO de idioma (opcional)    |

**Respuesta:** `{"text": "...", "language": "en", "duration": 2.5}`

## Uso desde n8n

### TTS
- Method: `POST`
- URL: `http://kokoro:5000/tts`
- Body Type: `Form-Data`
- Campos: `text`, `voice`, `speed`, `fmt`
- Response Format: `File` (guardar como Binary Data para enviar a WhatsApp)

### STT
- Method: `POST`
- URL: `http://kokoro:5000/stt`
- Body Type: `Form-Data`
- Campo `file`: archivo de audio (desde nodo anterior)
- Response: parsear JSON → `{{ $json.text }}`

## Voces disponibles

### Kokoro — Inglés (US) — 7 voces
| Clave API             | Voz interna   | Descripción               |
|-----------------------|---------------|---------------------------|
| `en_us_female_bella`  | `af_bella`    | Bella — femenino (US)     |
| `en_us_female_sarah`  | `af_sarah`    | Sarah — femenino (US)     |
| `en_us_female_nicole` | `af_nicole`   | Nicole — femenino (US)    |
| `en_us_female_sky`    | `af_sky`      | Sky — femenino (US)       |
| `en_us_male_adam`     | `am_adam`     | Adam — masculino (US)     |
| `en_us_male_michael`  | `am_michael`  | Michael — masculino (US)  |
| `en_us_male_liam`     | `am_liam`     | Liam — masculino (US)     |

### Kokoro — Inglés (UK) — 4 voces
| Clave API               | Voz interna    | Descripción                |
|-------------------------|----------------|----------------------------|
| `en_gb_female_emma`     | `bf_emma`      | Emma — femenino (UK)       |
| `en_gb_female_isabella` | `bf_isabella`  | Isabella — femenino (UK)   |
| `en_gb_male_george`     | `bm_george`    | George — masculino (UK)    |
| `en_gb_male_lewis`      | `bm_lewis`     | Lewis — masculino (UK)     |

### Edge TTS — Español — 5 voces
| Clave API             | Voz Edge TTS             | Descripción                       |
|-----------------------|--------------------------|-----------------------------------|
| `es_es_female_elvira` | `es-ES-ElviraNeural`     | Elvira — femenino (España)        |
| `es_es_male_alvaro`   | `es-ES-AlvaroNeural`     | Álvaro — masculino (España)       |
| `es_mx_female_dalia`  | `es-MX-DaliaNeural`      | Dalia — femenino (México)         |
| `es_mx_male_jorge`    | `es-MX-JorgeNeural`      | Jorge — masculino (México)        |
| `es_ar_female_elena`  | `es-AR-ElenaNeural`      | Elena — femenino (Argentina)      |

## Gestión de errores

| Código | Significado                    |
|--------|--------------------------------|
| 400    | Voz desconocida                |
| 500    | Error generando audio (interno)|

## Estado del despliegue

- [x] TTS inglés (Kokoro) — calidad excelente, local, sin internet
- [x] TTS español (Edge TTS) — calidad excelente, requiere internet
- [x] STT multilingüe (faster-whisper)
- [x] Conversión de formatos vía ffmpeg
- [x] Integración con red Docker interna
- [ ] Rate limiting (pendiente)
- [ ] Validación de tamaño de inputs (pendiente)

## Seguridad

**No hay puertos expuestos al host.** El contenedor solo es accesible desde
la red Docker `esoter_net`. Sin autenticación ni rate limiting — el riesgo es
bajo porque solo servicios controlados (n8n, crewai) tienen acceso.

Riesgos documentados:
- Sin límite de tamaño en STT: añadir límite de ~10MB si se requiere
- Sin rate limiting: añadir middleware si hay preocupación por abuso
- Sin límite de caracteres en TTS: añadir ~2000 chars si se requiere

## Costes

**$0.** Todo el stack es open-source y corre en el servidor. Edge TTS usa la
API gratuita de Microsoft sin necesidad de API key.

## Archivos del módulo
```
kokoro/
├── Dockerfile    # Imagen Python 3.12-slim + dependencias
├── app.py        # API FastAPI con ambos backends
└── README.md     # Este archivo
```
