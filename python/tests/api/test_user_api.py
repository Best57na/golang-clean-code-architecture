import pytest

USERS = "/api/v1/users"
EMAIL = "somchai@example.com"
PASSWORD = "super-secret-1"


def register(client, email=EMAIL, password=PASSWORD):
    return client.post(
        f"{USERS}/register",
        json={"email": email, "password": password, "first_name": "Somchai", "last_name": "J"},
    )


def login(client, email=EMAIL, password=PASSWORD):
    return client.post(f"{USERS}/login", json={"email": email, "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tokens(client) -> dict[str, str]:
    register(client)
    return login(client).json()["token"]


def test_register_returns_user_without_password(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == EMAIL
    assert "password" not in body


def test_register_duplicate_email_returns_409(client):
    register(client)

    response = register(client)

    assert response.status_code == 409
    assert response.json() == {"trace_id": "users-001", "message": "email has been used"}


@pytest.mark.parametrize(
    ("email", "password", "field"),
    [("not-an-email", PASSWORD, "email"), (EMAIL, "short", "password")],
)
def test_register_validates_body(client, email, password, field):
    response = register(client, email=email, password=password)

    assert response.status_code == 400
    assert response.json()["trace_id"] == "middleware-003"
    assert response.json()["message"].startswith(field)


def test_login_returns_user_and_tokens(client):
    register(client)

    response = login(client)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == EMAIL
    assert set(response.json()["token"]) == {"access", "refresh"}


def test_login_errors_do_not_reveal_whether_email_exists(client):
    register(client)

    wrong_password = login(client, password="wrong-password")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


@pytest.mark.parametrize("method", ["get", "post"])
def test_profile_with_access_token(client, tokens, method):
    response = getattr(client, method)(f"{USERS}/profile", headers=bearer(tokens["access"]))

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


def test_profile_without_token_returns_401(client):
    response = client.get(f"{USERS}/profile")

    assert response.status_code == 401
    assert response.json()["trace_id"] == "middleware-002"


def test_profile_rejects_refresh_token(client, tokens):
    response = client.get(f"{USERS}/profile", headers=bearer(tokens["refresh"]))

    assert response.status_code == 401


def test_refresh_token_revokes_old_access_token(client, tokens):
    response = client.post(f"{USERS}/refresh-token", json={"refresh_token": tokens["refresh"]})

    assert response.status_code == 200
    new_access = response.json()["token"]["access"]
    assert client.get(f"{USERS}/profile", headers=bearer(new_access)).status_code == 200
    assert client.get(f"{USERS}/profile", headers=bearer(tokens["access"])).status_code == 401


def test_logout_revokes_tokens(client, tokens):
    response = client.post(f"{USERS}/logout", json={"refresh_token": tokens["refresh"]})

    assert response.status_code == 204
    assert client.get(f"{USERS}/profile", headers=bearer(tokens["access"])).status_code == 401
    refresh = client.post(f"{USERS}/refresh-token", json={"refresh_token": tokens["refresh"]})
    assert refresh.status_code == 401
    assert refresh.json()["trace_id"] == "users-003"
