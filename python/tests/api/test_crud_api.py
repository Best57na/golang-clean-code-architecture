import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.interface.repositories.postgres.models import UserModel, UserPermissionModel

DATA = "/api/v1/data"
PASSWORD = "super-secret-1"


def create_user(client, email: str) -> None:
    response = client.post(
        "/api/v1/users/register",
        json={"email": email, "password": PASSWORD, "first_name": "F", "last_name": "L"},
    )
    assert response.status_code == 201


def login_headers(client, email: str) -> dict[str, str]:
    response = client.post("/api/v1/users/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {response.json()['token']['access']}"}


def grant(engine, email: str, permission: str) -> None:
    with Session(engine) as session:
        user_id = session.scalar(select(UserModel.id).where(UserModel.email == email))
        session.add(UserPermissionModel(user_id=user_id, permission=permission))
        session.commit()


@pytest.fixture
def admin(client, engine) -> dict[str, str]:
    create_user(client, "admin@example.com")
    grant(engine, "admin@example.com", "admin")
    for i in range(1, 4):
        create_user(client, f"user{i}@example.com")
    return login_headers(client, "admin@example.com")


def test_requires_bearer_token(client):
    response = client.get(f"{DATA}/users")

    assert response.status_code == 401
    assert response.json()["trace_id"] == "middleware-002"


def test_non_admin_gets_403(client):
    create_user(client, "viewer@example.com")

    response = client.get(f"{DATA}/users", headers=login_headers(client, "viewer@example.com"))

    assert response.status_code == 403
    assert response.json() == {"trace_id": "crud-003", "message": "permission denied"}


def test_list_paginates_and_hides_password(client, admin):
    response = client.get(f"{DATA}/users", params={"_page": 2, "_pageSize": 3}, headers=admin)

    assert response.status_code == 200
    body = response.json()
    assert (body["page"], body["page_size"], body["total_data"], body["total_page"]) == (
        2,
        3,
        4,
        2,
    )
    assert [row["email"] for row in body["data"]] == ["user3@example.com"]
    assert "password" not in body["data"][0]


def test_list_accepts_trailing_slash_like_go_route(client, admin):
    response = client.get(f"{DATA}/users/", headers=admin)

    assert response.status_code == 200
    assert response.json()["total_data"] == 4


def test_list_filters_by_field(client, admin):
    response = client.get(f"{DATA}/users", params={"email": "user2@example.com"}, headers=admin)

    assert response.json()["total_data"] == 1


def test_list_rejects_filter_on_hidden_field(client, admin):
    response = client.get(f"{DATA}/users", params={"password": "x"}, headers=admin)

    assert response.status_code == 400
    assert response.json()["trace_id"] == "crud-002"


def test_retrieve_one(client, admin):
    response = client.get(f"{DATA}/users/1", headers=admin)

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "admin@example.com"
    assert response.json()["data_schema"]["name"] == "users"


def test_retrieve_missing_returns_404(client, admin):
    response = client.get(f"{DATA}/users/999", headers=admin)

    assert response.status_code == 404
    assert response.json() == {"trace_id": "crud-001", "message": "data not found"}


def test_describe(client, admin):
    response = client.get(f"{DATA}/user-permissions/describe", headers=admin)

    assert response.status_code == 200
    assert {"name": "permission", "type": "string"} in response.json()["fields"]


def test_user_tokens_are_not_exposed(client, admin):
    response = client.get(f"{DATA}/user-tokens", headers=admin)

    assert response.status_code == 404
    assert response.json()["message"] == "entity model not found"
