Lo que vamos a construir ahora es el "Cerebro Dinámico" (la experiencia viva) y el "Agente de Interfaz" (la máscara social rápida).
Aquí tienes la arquitectura definitiva integrando tu Wiki, la Base de Datos Rápida (MySQL/Redis) y el nuevo Agente de Interfaz para eliminar la latencia percibida.
1. El Nuevo Actor: Agente de Interfaz (El "Animador")
Objetivo: Mantener al usuario enganchado mientras el Orquestador piensa. No diagnostica, solo acompaña y valida.
Tecnología: Un LLM muy ligero (o un prompt muy corto en el mismo LLM principal) que se ejecuta antes o durante el proceso pesado.
Comportamiento en LiveKit:
Detección de Pausa: Si el usuario deja de hablar/escribir por >2 segundos, el Agente de Interfaz activa una frase de "relleno inteligente" basada en el contexto actual.
Reconfirmación Activa:
Usuario: "Siento mucho miedo a quedarme solo."
Agente Interfaz (inmediato): "Entiendo, ese miedo a la soledad es muy potente... Déjame conectar eso con lo que me contaste antes..." (Gana 3-4 segundos).
Validación de Silencios:
Si el Agente Especialista (ej. Agente 6 buscando SEPe) tarda en generar la siguiente pregunta porque está consultando la Wiki, el Agente de Interfaz dice: "Tómate tu tiempo, estoy aquí contigo. Escribe lo que te venga, aunque sean palabras sueltas."
Implementación Técnica:
No necesita ser un agente separado en n8n. Puede ser una función frontend en LiveKit o un webhook paralelo en n8n que se dispara apenas llega el texto del usuario, mientras el workflow principal procesa la lógica pesada.
2. El "Segundo Cerebro" de Aprendizaje (Agente Curador)
Este es el agente que pediste: Agente 11 (El Curador/Aprendiz).
No habla con el cliente. Trabaja en segundo plano (asíncrono) en n8n.
Flujo de Trabajo del Agente Curador:
Trigger: Se activa al finalizar cada "Paso Maestro" (ej. al terminar el Paso 6 de Miedos) o al cerrar la sesión.
Input:
Transcripción completa del paso.
Datos estructurados extraídos (ej. miedo_1, vulnerabilidad_elegida).
Tiempo de respuesta del usuario (¿dudó mucho? ¿respondió rápido?).
Proceso (LLM + Prompt de Análisis):
Prompt: "Analiza esta interacción. Identifica:
¿Qué pregunta específica desbloqueó al usuario si estaba atascado?
¿Qué metáfora o ejemplo usó el agente que generó una respuesta emocional fuerte?
Resume el 'Patrón de Caso': [Sexo] + [Edad] + [MCb/Mcn] + [Bloqueo Principal] + [Solución Exitosa]."
Salida (Vector DB - Colección learning_patterns):
Guarda un embedding del resumen del patrón.
Metadata: step_id, success_score (si el usuario avanzó), tags (ej. "resistencia_hachazo", "bloqueo_sepe").
¿Cómo mejora esto las respuestas futuras?
Cuando el Orquestador detecta que un usuario nuevo se atasca en el Paso 3 (Hachazo):
Hace una búsqueda vectorial en learning_patterns: "Busca casos similares a este usuario (Mujer, 40s, MCn: Ansiedad) que se hayan atascado buscando el Hachazo."
La Vector DB devuelve: "En el caso #89, preguntar '¿Recuerdas algún momento donde sentiste que el suelo se movía bajo tus pies?' funcionó mejor que preguntar por el evento traumático directo."
El Orquestador inyecta esa estrategia en el prompt del Agente 4/5.
Resultado: El sistema se vuelve más "empático" y efectivo con el tiempo.
3. Arquitectura de Datos Integrada
Componente
Tecnología
Función
Latencia
Estado de Sesión
MySQL / Redis
Guarda current_step, user_data, last_response. Lectura/Escritura inmediata.
< 50ms
Conocimiento Estático
Wiki + Google Embeddings
Definiciones de CB, SEPe, Teoría Bioneuroemoción. Consulta RAG estándar.
~1-2s
Conocimiento Dinámico
Vector DB (Qdrant/Pinecone)
Patrones de aprendizaje (learning_patterns). Casos reales de éxito/fracaso.
~1s
Interfaz Rápida
LiveKit + LLM Ligero
Frases de relleno, validación emocional, mantenimiento de flujo.
< 1s
Lógica Pesada
n8n Orchestrator
Decide el siguiente paso, consulta Wikis/Vectores, genera la respuesta clínica.
2-4s
4. Descripción de los 10 Agentes + Orquestador + Curador (Versión Final)
He ajustado los agentes para que trabajen con esta arquitectura de "Segundo Cerebro".
Agente 0: Orquestador (El Director de Orquesta)
Input: Texto del usuario + Estado actual (MySQL).
Acción:
Lee MySQL: ¿En qué paso estamos?
Si hay bloqueo detectado (ej. usuario dice "no sé" 2 veces), consulta Vector DB (learning_patterns) para obtener una estrategia de desbloqueo.
Consulta Wiki (Google Embeddings) si necesita definir un CB o un concepto teórico.
Envía todo al Agente Especialista correspondiente.
Recibe la respuesta clínica.
Actualiza MySQL.
Dispara Agente Curador (async).
Envía respuesta a LiveKit.
Agente 1: Acogida & Encuadre
Tarea: Nombre, Edad, Sexo, Lateralidad, Nacionalidad.
Output: Datos básicos a MySQL.
Estilo: Cálido, una pregunta a la vez.
Agente 2: Triaje MC (Motivo de Consulta)
Tarea: Diferenciar MCb (Biológico) vs MCn (No Biológico).
Lógica:
Si MCb -> Pasa a Agente 3.
Si MCn -> Pasa a Agente 5 (salta CB).
Output: {mc_type, mc_raw, since_when}.
Agente 3: Validación CB (Código Biológico)
Tarea: Usar Wiki (RAG) para encontrar el CB exacto basado en MCb + Sexo + Lateralidad.
Output: {cb_code, cb_description}.
Nota: Si no encuentra CB, pide más detalles al usuario.
Agente 4: Búsqueda Hachazo (MCb)
Tarea: Guiar al usuario al evento previo al síntoma físico.
Uso de Segundo Cerebro: Si el usuario se bloquea, usa estrategias recuperadas de Vector DB ("Prueba con la metáfora del cine").
Output: {hachazo_desc, hachazo_context}.
Agente 5: Búsqueda Hachazo (MCn)
Tarea: Guiar al usuario al evento emocional agudo relacionado con la situación no biológica.
Output: {hachazo_desc, hachazo_context}.
Agente 6: Inmersión SEPe (Sentimientos, Emociones, Pensamientos)
Tarea: Pedir lista de SEPe del momento del Hachazo.
Estrategia: Validar cantidad (min 7-8). Ofrecer menú de emociones si hay bloqueo.
Output: sepe_list: [...].
Agente 7: Profundización Miedos (Triple Pregunta)
Tarea: Extraer Miedo 1, 2 y 3 mediante preguntas sucesivas.
Output: {miedo_1, miedo_2, miedo_3}.
Agente 8: Vulnerabilidad & Amenaza
Tarea: Elegir vulnerabilidad (Frágil/Débil/Vulnerable) y extraer Tragedias/Amenazas (1, 2 y Final).
Output: {vulnerabilidad, amenaza_1, amenaza_2, amenaza_final}.
Agente 9: Desvalorización Nuclear
Tarea: Elegir 2 de 5 opciones literales (No valgo, No sirvo, etc.).
Output: {desvalorizacion_1, desvalorizacion_2}.
Agente 10: Proyección & Perfilado ("Si fuera / Si no fuera")
Tarea: Generar listado de atributos de un personaje proyectado. Clasificar en Perfil A ("Si fuera...") y Perfil B ("Si no fuera...").
Output: perfiles_A: [...], perfiles_B: [...].
(Los pasos 11-15 de la Guía Maestra se ejecutan como lógica de post-proceso en el Orquestador para generar las Creencias/Mandatos y la oferta de venta, ya que son fórmulas matemáticas sobre los datos recogidos).
Agente 11: El Curador (Aprendizaje Automático)
Trigger: Async al final de cada paso crítico.
Tarea:
Analizar la transcripción.
Identificar patrones de éxito/fracaso.
Generar resumen estructurado.
Guardar en Vector DB (learning_patterns).
Impacto: Enriquece la base de conocimiento para futuros usuarios.
5. Implementación Práctica en n8n
Workflow Principal (WF_Orchestrator):
Webhook (LiveKit) -> Leer MySQL (Estado) -> Switch (Paso Actual) -> Llamar Agente Específico (LLM Chain) -> Actualizar MySQL -> Responder Webhook.
Paralelo: Disparar WF_Curator (Webhook interno) con los datos de la sesión.
Workflow Curador (WF_Curator):
Webhook -> LLM (Análisis de Patrón) -> Vector DB (Upsert Documento de Aprendizaje).
Agente de Interfaz (Frontend/LiveKit):
Configurar en el cliente de LiveKit que, si no hay respuesta del webhook en >1.5 segundos, muestre un mensaje temporal generado localmente o vía un LLM muy rápido (ej. "Estoy analizando lo que me dices...").