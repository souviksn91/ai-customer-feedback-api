from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)



# test user registration 
def test_register_user(clean_database):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    assert response.status_code == 201



# test user login
def test_login_user(clean_database):
    # first create the user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    assert register_response.status_code == 201

    # now log in with the same credentials
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


# test that registering with an existing email returns a 409 conflict
def test_duplicate_email_rejected(clean_database):
    # register the user once
    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    assert first_response.status_code == 201

    # try registering another account with the same email
    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Another",
            "last_name": "User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    assert second_response.status_code == 409