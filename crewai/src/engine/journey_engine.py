import json
import os
import re
import httpx
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from jinja2 import Template
from src.config import get_settings

logger = logging.getLogger(__name__)

class JourneyEngine:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.journeys_path = "journeys"

    def _load_journey_file(self, journey_id: str) -> Dict[str, Any]:
        file_path = os.path.join(self.journeys_path, f"{journey_id}.json")
        if not os.path.exists(file_path):
            # Try absolute path if relative fails
            file_path = os.path.join(os.getcwd(), "crewai", "journeys", f"{journey_id}.json")

        if not os.path.exists(file_path):
             # Fallback for different environments
             file_path = f"/app/journeys/{journey_id}.json"

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def _call_rag(self, query: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/rag/search",
                    json={"query": query, "limit": 3}
                )
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    return "\n\n".join([r.get("content", "") for r in results])
        except Exception as e:
            logger.error(f"Error calling RAG: {e}")
        return ""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        # Try to find JSON in code blocks
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find anything that looks like a JSON object
        match = re.search(r"({.*})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return {}

    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        if condition == "default":
            return True
        try:
            # Simple expression evaluator for conditions like "mc_type == 'biological'"
            # We use a safe subset of eval or a simple parser.
            # For this task, we'll use a basic replacement and eval approach.
            # WARNING: eval is dangerous, but in this controlled JSON spec it's often used.
            # A better way would be a DSL parser.
            return eval(condition, {"__builtins__": {}}, data)
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    async def execute_step(
        self,
        journey_id: str,
        current_step_num: int,
        user_message: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        journey = self._load_journey_file(journey_id)
        step_config = next((s for s in journey["steps"] if s["step"] == current_step_num), None)

        if not step_config:
            raise ValueError(f"Step {current_step_num} not found in journey {journey_id}")

        rag_context = ""
        if "rag_query" in step_config:
            # Render rag_query template if it has variables
            query_template = Template(step_config["rag_query"])
            rendered_query = query_template.render(user_message=user_message, session_data=session_data)
            rag_context = await self._call_rag(rendered_query)

        # Render user prompt
        user_prompt_template = Template(step_config["user_prompt_template"])
        user_prompt = user_prompt_template.render(
            user_message=user_message,
            session_data=session_data,
            rag_context=rag_context
        )

        # Call LLM
        llm_config = step_config["llm"]
        response = await self.client.chat.completions.create(
            model=llm_config["model"],
            messages=[
                {"role": "system", "content": step_config["system_prompt"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 1000)
        )

        full_text = response.choices[0].message.content
        extracted_data = self._extract_json(full_text)

        # Clean response text (remove JSON block)
        clean_text = re.sub(r"```json\s*.*?\s*```", "", full_text, flags=re.DOTALL).strip()
        if not clean_text:
            clean_text = re.sub(r"{.*}", "", full_text, flags=re.DOTALL).strip()

        # Update session data with new extracted data
        updated_session_data = {**session_data, **extracted_data}

        # Determine next step
        next_step = current_step_num
        transitions = step_config["transitions"]

        # Check conditional transitions first
        found_transition = False
        for cond, target in transitions.items():
            if cond != "default" and self._evaluate_condition(cond, updated_session_data):
                next_step = target
                found_transition = True
                break

        # Fallback to default
        if not found_transition and "default" in transitions:
            next_step = transitions["default"]

        return {
            "response_text": clean_text or full_text,
            "extracted_data": extracted_data,
            "next_step": next_step,
            "updated_session_data": updated_session_data
        }
