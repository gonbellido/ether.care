import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock settings and its dependencies
mock_settings = MagicMock()
mock_settings.deepseek_api_key = "fake_key"

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.engine.journey_engine import JourneyEngine

async def test_engine_loading():
    with patch('src.engine.journey_engine.get_settings', return_value=mock_settings):
        engine = JourneyEngine()
        # Adjust path for testing
        engine.journeys_path = os.path.join(parent_dir, "journeys")
        journey = engine._load_journey_file("diagnostico_psicologico_v1")
        assert journey["journey_id"] == "diagnostico_psicologico_v1"
        assert len(journey["steps"]) == 10

async def test_extraction():
    with patch('src.engine.journey_engine.get_settings', return_value=mock_settings):
        engine = JourneyEngine()
        text = "Hola! ```json\n{\"nombre\": \"Juan\"}\n```"
        data = engine._extract_json(text)
        assert data["nombre"] == "Juan"

async def test_condition_evaluation():
    with patch('src.engine.journey_engine.get_settings', return_value=mock_settings):
        engine = JourneyEngine()
        data = {"mc_type": "biological"}
        assert engine._evaluate_condition("mc_type == 'biological'", data) is True

if __name__ == "__main__":
    asyncio.run(test_engine_loading())
    asyncio.run(test_extraction())
    asyncio.run(test_condition_evaluation())
    print("Tests passed!")
