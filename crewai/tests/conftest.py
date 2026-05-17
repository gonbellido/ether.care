import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10.0)

@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as ac:
        yield ac
