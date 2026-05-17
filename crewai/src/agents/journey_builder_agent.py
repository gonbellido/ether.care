import json
import re
import os
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema
from openai import AsyncOpenAI
from src.config import get_settings

class JourneyBuilderAgent:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1"
        )

        # Determine the base directory for journeys
        # If running in the container, it might be /app/journeys
        # If running from the repo root, it's crewai/journeys
        self.base_dir = Path("crewai/journeys")
        if not self.base_dir.exists() and os.path.exists("/app/journeys"):
            self.base_dir = Path("/app/journeys")
        elif not self.base_dir.exists() and Path("journeys").exists():
            self.base_dir = Path("journeys")

        self.schema_path = self.base_dir / "schema.json"

    async def generate_journey(self, description: str, journey_id: str) -> Dict[str, Any]:
        """
        Generates a journey JSON spec from a natural language description.
        Validates against schema.json and saves it to a file.
        """
        # Validate journey_id slug format
        if not re.match(r"^[a-z0-9-]+$", journey_id):
            raise ValueError("journey_id must be in slug format (lowercase, numbers, and hyphens only)")

        if not self.schema_path.exists():
            # If still not found, try to find it relative to this file
            alt_path = Path(__file__).parent.parent.parent / "journeys" / "schema.json"
            if alt_path.exists():
                self.schema_path = alt_path
                self.base_dir = alt_path.parent
            else:
                raise FileNotFoundError(f"Schema file not found at {self.schema_path} or {alt_path}")

        with open(self.schema_path, "r") as f:
            schema_content = json.load(f)

        system_prompt = f"""
Eres un experto arquitecto de sistemas multi-agente y especialista en diseño de flujos conversacionales.
Tu tarea es generar una especificación de 'journey' en formato JSON basada en una descripción en lenguaje natural.

La especificación debe seguir estrictamente el siguiente esquema JSON:
{json.dumps(schema_content, indent=2)}

Instrucciones:
1. Analiza la descripción del journey proporcionada por el usuario.
2. Define los pasos (steps) necesarios para cumplir con el journey de forma coherente.
3. Para cada paso, define un 'role', 'goal' y 'backstory' detallados y apropiados para un agente de CrewAI.
4. El 'journey_id' en el JSON resultante DEBE ser exactamente '{journey_id}'.
5. Devuelve ÚNICAMENTE el objeto JSON válido. No incluyas explicaciones adicionales, ni bloques de código markdown (como ```json ... ```).
"""

        user_message = f"Descripción del journey: {description}\njourney_id: {journey_id}"

        try:
            journey_json = await self._call_claude(system_prompt, user_message)

            try:
                jsonschema.validate(instance=journey_json, schema=schema_content)
            except jsonschema.ValidationError as e:
                # Retry once with error message
                retry_message = (
                    f"El JSON generado anteriormente no es válido según el esquema.\n"
                    f"Error de validación: {str(e)}\n"
                    f"Por favor, genera el JSON de nuevo corrigiendo los errores y asegurándote de que sea un objeto JSON puro."
                )
                journey_json = await self._call_claude(system_prompt, user_message + "\n\n" + retry_message)
                jsonschema.validate(instance=journey_json, schema=schema_content)

            # Save to file
            output_path = self.base_dir / f"{journey_id}.json"
            self.base_dir.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(journey_json, f, indent=2)

            return journey_json

        except Exception as e:
            # Re-raise or handle appropriately
            raise Exception(f"Error generating or validating journey: {str(e)}")

    async def _call_claude(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        response = await self.client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        content = response.choices[0].message.content.strip()

        # Attempt to extract JSON if Claude included other text
        json_match = re.search(r"(\{.*\})", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try parsing the whole content
        return json.loads(content)
