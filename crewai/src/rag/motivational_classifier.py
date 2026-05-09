"""
Clasificador de chunks motivacionales usando DeepSeek (bajo coste).
Analiza cada chunk de texto y determina si es apto para envío proactivo,
su tipo, temas, estados emocionales y nivel de profundidad.
"""
import json
from openai import OpenAI
from src.config import get_settings

import structlog
log = structlog.get_logger()

SYSTEM_PROMPT = """Eres un clasificador de contenido esotérico y espiritual.
Analiza el siguiente fragmento de texto y determina si es apto para enviarse
de forma proactiva a clientes como mensaje motivacional o de acompañamiento espiritual.

Responde SOLO con un JSON válido con esta estructura exacta:
{
  "is_motivational": true/false,
  "motivational_type": "inspiracion|ensenanza|reflexion|ritual_sugerido|afirmacion|prediccion_general|null",
  "topics": ["amor", "trabajo", "dinero", "familia", "salud", "espiritualidad", "bloqueos", "transicion"],
  "emotional_states": ["ansiedad", "bloqueo", "esperanza", "duelo", "confusion", "gratitud", "miedo", "fuerza"],
  "depth_level": 1,
  "confidence": 0.85
}

Criterios:
- is_motivational: true si el fragmento contiene una enseñanza, reflexión, afirmación,
  consejo espiritual o mensaje inspirador que tenga valor por sí solo
- motivational_type: el tipo más adecuado (null si is_motivational es false)
- topics: lista de temas relevantes del fragmento (máx 3)
- emotional_states: estados emocionales para los que es útil (máx 3)
- depth_level: 1=introductorio (sin conocimiento previo), 2=intermedio, 3=avanzado
- confidence: tu nivel de confianza en la clasificación (0.0-1.0)

NO añadas texto fuera del JSON."""


def classify_chunk(chunk_text: str) -> dict:
    """
    Clasifica un chunk de texto como motivacional o no.
    Retorna dict con los campos del SYSTEM_PROMPT.
    """
    settings = get_settings()

    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com"
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Fragmento a clasificar:\n\n{chunk_text[:1500]}"}
            ],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        log.error("Error clasificando chunk", error=str(e))
        return {
            "is_motivational": False,
            "motivational_type": None,
            "topics": [],
            "emotional_states": [],
            "depth_level": 1,
            "confidence": 0.0
        }


def classify_chunks_batch(chunks: list[str]) -> list[dict]:
    """Clasifica múltiples chunks. Retorna lista de clasificaciones."""
    results = []
    for i, chunk in enumerate(chunks):
        log.info("Clasificando chunk", idx=i+1, total=len(chunks))
        result = classify_chunk(chunk)
        results.append(result)
    return results
