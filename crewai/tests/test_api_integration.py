# Run against: http://localhost:8000
# Start API first: cd crewai && uvicorn src.api.main:app --port 8000

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_rag_search_returns_results_key(client):
    r = client.post("/rag/search", json={"query": "tarot amor", "limit": 3})
    assert r.status_code == 200
    assert "results" in r.json()

def test_journey_get_new_session(client):
    r = client.get("/journey/nonexistent-session-xyz")
    assert r.status_code == 200
    data = r.json()
    assert data["step"] == 1
    assert data["status"] == "new"

def test_journey_execute_missing_fields(client):
    r = client.post("/journey/execute", json={})
    assert r.status_code == 422  # Pydantic validation error

def test_journey_build_requires_admin_key(client):
    r = client.post("/journey/build", json={"description": "test", "journey_id": "test"})
    assert r.status_code == 403
