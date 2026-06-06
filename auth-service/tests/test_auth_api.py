import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_me_success_flow(client: AsyncClient) -> None:
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "stringst",
        },
    )

    assert register_response.status_code == 201

    registered_user = register_response.json()

    assert registered_user["email"] == "user@example.com"
    assert registered_user["role"] == "user"
    assert "id" in registered_user
    assert "created_at" in registered_user
    assert "password_hash" not in registered_user

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "user@example.com",
            "password": "stringst",
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    assert login_response.status_code == 200

    token_data = login_response.json()

    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]

    access_token = token_data["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200

    current_user = me_response.json()

    assert current_user["email"] == "user@example.com"
    assert current_user["role"] == "user"
    assert "password_hash" not in current_user


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "password": "stringst",
    }

    first_response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["error_code"] == "user_already_exists"


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={
            "email": "wrong-password@example.com",
            "password": "stringst",
        },
    )

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "wrong-password@example.com",
            "password": "wrongpass",
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    assert login_response.status_code == 401

    data = login_response.json()

    assert data["error_code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid.token.value",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["error_code"] == "invalid_token"
