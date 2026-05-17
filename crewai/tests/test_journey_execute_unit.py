import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import ASGITransport, AsyncClient
from src.api.main import app

@pytest.mark.asyncio
async def test_execute_calls_engine():
    mock_result = {
        "response_text": "Hola, bienvenido",
        "next_step": 1,
        "extracted_data": {},
        "updated_session_data": {}
    }
    mock_state = {"step": 1, "status": "new", "data": {}}
    mock_journey = {"steps": [{"step": 1, "name": "Acogida & Perfilado"}]}

    # Mock the classes themselves, not the instances inside the route
    with patch("src.api.main.JourneyManager") as MockJM,          patch("src.api.main.JourneyEngine") as MockEngine:

        mock_jm = MagicMock()
        mock_jm.get_session_state = AsyncMock(return_value=mock_state)
        mock_jm.update_session_state = AsyncMock()
        MockJM.return_value = mock_jm

        mock_engine = MagicMock()
        mock_engine.execute_step = AsyncMock(return_value=mock_result)
        mock_engine.load_journey = MagicMock(return_value=mock_journey)
        MockEngine.return_value = mock_engine

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/journey/execute", json={
                "journey_id": "diagnostico_psicologico_v1",
                "session_id": "test-session",
                "user_id": "test-user",
                "user_message": "Hola"
            })

        assert r.status_code == 200
        assert r.json()["response_text"] == "Hola, bienvenido"
        assert r.json()["next_step"] == 1
