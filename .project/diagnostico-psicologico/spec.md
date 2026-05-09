# Especificación: Sistema de Diagnóstico Psicológico (Biodescodificación)

**Fecha**: 2026-04-24
**Stack**: LiveKit + n8n + MySQL + Qdrant + CrewAI

## Arquitectura General

```
[Usuario] → Audio → LiveKit (STT) → Texto
                                       ↓
                              n8n Orchestrator
                              ├─ Leer MySQL (estado)
                              ├─ Consultar Vector DB (si aplica)
                              ├─ Invocar Agente 1-10 (LLM)
                              └─ Escribir MySQL (nuevo estado)
                                       ↓
                              LiveKit (TTS) → Audio → [Usuario]
                                       
                              [Async] Agente Curador → Vector DB
```

## Estructura de Datos

### MySQL — `sessions` (Verdad Operativa)

```sql
CREATE TABLE sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    current_step INT DEFAULT 1,          -- 1-10
    status ENUM('active','paused','completed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_status (status)
);

CREATE TABLE session_state (
    session_id VARCHAR(64) PRIMARY KEY,
    data_json JSON NOT NULL,              -- progreso estructurado completo
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### Redis (Opcional) — Baja latencia durante conversación activa

- Clave: `session:{session_id}`
- Valor: JSON session_state
- TTL: 30 minutos (se vuelca a MySQL al cerrar sesión)

### Vector DB (Qdrant) — Colección `learning_patterns`

- Metadata: `mc_type`, `cb_code`, `edad`, `sexo`, `resultado_exito`
- Contenido: Resumen narrativo del caso + patrones de éxito
- Tags: `pattern_unlock_hachazo`, `case_study_cb_{code}`

## Los 12 Agentes

### Agente 0: Orquestador (Cerebro Central)
- **Trigger**: Webhook LiveKit (texto transcrito)
- **Acción**: Lee MySQL → decide paso → consulta Vector DB si aplica → llama agente → escribe MySQL → responde LiveKit → dispara Curador (async)

### Agente 1: Acogida & Perfilado (Paso 1)
- **Input**: Primer mensaje / datos faltantes
- **Tarea**: Extraer Nombre, Edad, Sexo, Lateralidad
- **Output**: `{nombre, edad, sexo, lateralidad}`

### Agente 2: Triaje MC (Paso 2)
- **Input**: Motivo de Consulta
- **Tarea**: Clasificar MCb vs MCn. Si MCb, pedir especificación.
- **Output**: `{mc_type: "biological"|"non_biological", mc_raw, cb_preliminar}`
- **Lógica**: MCn → salta a Agente 5. MCb → pasa a Agente 3.

### Agente 3: Validación CB (Paso 2.5 — Solo MCb)
- **Input**: MCb + Sexo + Lateralidad
- **Tarea**: Consultar Wiki/Vector DB para código biológico exacto
- **Output**: `{cb_code, cb_description}`
- **Error**: No encuentra CB → pedir más datos

### Agente 4: Búsqueda Hachazo MCb (Paso 3)
- **Input**: CB Description
- **Tarea**: Guiar al usuario al evento previo al síntoma
- **Output**: `{hachazo_desc, hachazo_timestamp_approx}`

### Agente 5: Búsqueda Hachazo MCn (Paso 3 Alternativo)
- **Input**: MCn Description
- **Tarea**: Guiar al usuario al evento emocional agudo
- **Output**: `{hachazo_desc, hachazo_timestamp_approx}`

### Agente 6: Extracción SEPe (Paso 4)
- **Input**: Hachazo identificado
- **Tarea**: Pedir Sentimientos/Emociones/Pensamientos (mín 7-8)
- **Output**: `{sepe_list: ["miedo", "angustia", ...]}`

### Agente 7: Profundización Miedos (Pasos 5-6)
- **Input**: SEPe List
- **Tarea**: "Triple Pregunta" → Miedo Nuclear
- **Output**: `{miedo_1, miedo_2, miedo_3}`

### Agente 8: Vulnerabilidad & Amenaza (Pasos 6-7)
- **Input**: Miedo 3
- **Tarea**: Elegir vulnerabilidad + 3 Amenazas
- **Output**: `{vulnerabilidad: "frágil"|"débil"|"vulnerable", amenaza_1, amenaza_2, amenaza_final}`

### Agente 9: Desvalorización Nuclear (Pasos 7-8)
- **Input**: Amenaza Final
- **Tarea**: 5 opciones literales, elegir 2
- **Output**: `{desvalorizacion_1, desvalorizacion_2}`

### Agente 10: Proyección & Perfilado (Paso 9)
- **Input**: Desvalorizaciones + Amenaza Final
- **Tarea**: Atributos "Si fuera..." / "Si no fuera..."
- **Output**: `{perfiles_A: [...], perfiles_B: [...]}`

### Agente 11: El Curador (Aprendizaje Automático)
- **Trigger**: Webhook n8n (post-sesión o post-paso crítico)
- **Input**: Transcripción + estado MySQL final
- **Tarea**: Resumir caso, identificar patrones, generar embedding
- **Output**: Upsert en Qdrant (colección `learning_patterns`)

## Flujo de Integración LiveKit

1. LiveKit envía audio → STT → texto
2. Webhook a n8n con texto + session_id
3. n8n lee MySQL (current_step, data_json) — <50ms
4. n8n decide qué agente toca (switch por current_step)
5. n8n construye prompt con datos MySQL + contexto Vector DB (si aplica)
6. n8n llama LLM (Groq/Llama-3-70b o DeepSeek)
7. n8n parsea respuesta, actualiza MySQL
8. n8n responde a LiveKit
9. LiveKit TTS → audio al usuario

### Truco: Respuesta Parcial
Si el proceso tarda >2s, un LLM rápido genera relleno ("Déjame procesar eso...") mientras n8n completa.

## Modelo de Negocio

Sistema de biodescodificación con 10 pasos de diagnóstico + perfilado final.
Cada paso es un agente especializado que extrae datos estructurados.
El Curador (agente 11) permite aprendizaje continuo del sistema.
