import pytest

pytestmark = pytest.mark.django_db

PASSWORD = "Str0ng-Pass!"


def register(api_client, **overrides):
    data = {
        "username": "bob",
        "email": "bob@example.com",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
        **overrides,
    }
    return api_client.post("/auth/register", data, format="json")


def test_registration_is_logged_without_password(api_client, caplog):
    response = register(api_client)

    assert response.status_code == 201
    assert f"User registered: id={response.json()['id']} username='bob'" in caplog.text
    assert PASSWORD not in caplog.text


def test_invalid_registration_logs_field_names_without_values(api_client, caplog):
    register(api_client, email="not-an-email", password="12345", password_confirm="12345")

    assert "Registration rejected: invalid fields ['email', 'password']" in caplog.text
    assert "not-an-email" not in caplog.text
    assert "12345" not in caplog.text


def test_login_is_logged_without_password_and_tokens(api_client, user, caplog):
    response = api_client.post("/auth/login", {"username": "alice", "password": PASSWORD}, format="json")

    assert response.status_code == 200
    assert "User logged in: username='alice'" in caplog.text
    assert PASSWORD not in caplog.text
    assert response.json()["access"] not in caplog.text
    assert response.json()["refresh"] not in caplog.text


def test_failed_login_is_logged_as_warning_without_password(api_client, user, caplog):
    response = api_client.post("/auth/login", {"username": "alice", "password": "wrong-secret"}, format="json")

    assert response.status_code == 401
    assert any(r.levelname == "WARNING" and r.getMessage() == "Failed login: username='alice'" for r in caplog.records)
    assert "wrong-secret" not in caplog.text


def test_failed_refresh_is_logged_without_token(api_client, caplog):
    response = api_client.post("/auth/refresh", {"refresh": "forged-refresh-token"}, format="json")

    assert response.status_code == 401
    assert "Token refresh failed: refresh token is invalid or expired" in caplog.text
    assert "forged-refresh-token" not in caplog.text
