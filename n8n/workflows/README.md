# Workflow n8n: WF_Diagnostico

Este workflow actúa como puente entre el agente de voz LiveKit y el motor de journeys de CrewAI.

## Instrucciones de Uso

### 1. Importación
- Abre la interfaz de n8n.
- Ve a **Workflows** -> **Import from file**.
- Selecciona el archivo `WF_Diagnostico.json`.

### 2. Activación
- Una vez importado, asegúrate de que todos los nodos estén configurados correctamente.
- Haz clic en el botón **Activate** en la esquina superior derecha.

### 3. URL del Webhook
- Tras la activación, el endpoint del webhook será:
  `POST https://n8n.ether.care/webhook/diagnostico`

### 4. Configuración en LiveKit Agent
Asegúrate de establecer la siguiente variable de entorno en el contenedor `livekit-agent`:
```bash
N8N_WEBHOOK_URL=http://n8n:5678/webhook/diagnostico
```

## Prueba de Funcionamiento

Puedes probar el flujo ejecutando el siguiente comando curl (asegúrate de que el workflow esté activo o en modo de prueba):

```bash
curl -X POST http://localhost:5678/webhook/diagnostico \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola, me llamo Juan","session_id":"test-room","user_id":"test"}'
```

El sistema debería responder con un JSON que contenga el campo `response`.
