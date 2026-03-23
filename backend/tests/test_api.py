# backend/tests/test_api.py
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_user@example.com",
            "password": "testpass123",
            "name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test_user@example.com"
    return data


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login_test@example.com", "password": "pass123", "name": "Login Test"},
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@example.com", "password": "pass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_wrong_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 403  # No Bearer token
