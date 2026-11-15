import pytest

from roadmap.models import Category

pytestmark = pytest.mark.django_db

MISSING_ID = 999999


# ---------- GET: доступно всім ----------


def test_list_categories_as_guest(api_client, category):
    response = api_client.get("/categories")

    assert response.status_code == 200
    assert response.json() == [
        {"id": category.id, "name": "Web", "description": "Вразливості вебзастосунків"},
    ]


def test_list_categories_empty(api_client):
    response = api_client.get("/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_retrieve_category_as_guest(api_client, category):
    response = api_client.get(f"/categories/{category.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Web"


def test_retrieve_missing_category_returns_404(api_client):
    response = api_client.get(f"/categories/{MISSING_ID}")

    assert response.status_code == 404


def test_list_task_types_of_category(api_client, category_with_task_type):
    response = api_client.get(f"/categories/{category_with_task_type.id}/task-types")

    assert response.status_code == 200
    assert [task_type["name"] for task_type in response.json()] == ["SQL Injection"]


# ---------- POST: лише авторизовані ----------


def test_create_category_authenticated(auth_client):
    response = auth_client.post("/categories", {"name": "Crypto", "description": "Криптографія"}, format="json")

    assert response.status_code == 201
    assert response.json()["name"] == "Crypto"
    assert Category.objects.filter(name="Crypto").exists()


def test_create_category_as_guest_returns_401(api_client):
    response = api_client.post("/categories", {"name": "Crypto"}, format="json")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided."
    assert not Category.objects.exists()


def test_create_category_with_invalid_token_returns_401(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid")

    response = api_client.post("/categories", {"name": "Crypto"}, format="json")

    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"
    assert not Category.objects.exists()


def test_create_category_with_expired_token_returns_401(expired_token_client):
    response = expired_token_client.post("/categories", {"name": "Crypto"}, format="json")

    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"
    assert not Category.objects.exists()


@pytest.mark.parametrize(
    "payload",
    [
        {"description": "Без назви"},
        {"name": ""},
        {"name": "x" * 101},
    ],
    ids=["missing-name", "empty-name", "too-long-name"],
)
def test_create_category_with_invalid_data_returns_400(auth_client, payload):
    response = auth_client.post("/categories", payload, format="json")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid data."
    assert "name" in response.json()["errors"]
    assert not Category.objects.exists()


def test_create_duplicate_category_returns_400(auth_client, category):
    response = auth_client.post("/categories", {"name": "Web"}, format="json")

    assert response.status_code == 400
    assert "name" in response.json()["errors"]
    assert Category.objects.count() == 1


# ---------- PUT: лише авторизовані ----------


def test_update_category_authenticated(auth_client, category):
    response = auth_client.put(f"/categories/{category.id}", {"name": "Web", "description": "Новий опис"}, format="json")

    assert response.status_code == 200
    category.refresh_from_db()
    assert category.description == "Новий опис"


def test_update_category_as_guest_returns_401(api_client, category):
    response = api_client.put(f"/categories/{category.id}", {"name": "Hacked"}, format="json")

    assert response.status_code == 401
    category.refresh_from_db()
    assert category.name == "Web"


def test_update_missing_category_returns_404(auth_client):
    response = auth_client.put(f"/categories/{MISSING_ID}", {"name": "Web"}, format="json")

    assert response.status_code == 404


def test_update_category_with_invalid_data_returns_400(auth_client, category):
    response = auth_client.put(f"/categories/{category.id}", {"name": ""}, format="json")

    assert response.status_code == 400
    assert "name" in response.json()["errors"]
    category.refresh_from_db()
    assert category.name == "Web"


# ---------- DELETE: лише авторизовані, і лише порожню категорію ----------


def test_delete_empty_category(auth_client, category):
    response = auth_client.delete(f"/categories/{category.id}")

    assert response.status_code == 204
    assert not Category.objects.filter(id=category.id).exists()


def test_delete_category_as_guest_returns_401(api_client, category):
    response = api_client.delete(f"/categories/{category.id}")

    assert response.status_code == 401
    assert Category.objects.filter(id=category.id).exists()


def test_delete_missing_category_returns_404(auth_client):
    response = auth_client.delete(f"/categories/{MISSING_ID}")

    assert response.status_code == 404


def test_delete_category_with_task_types_returns_409(auth_client, category_with_task_type):
    response = auth_client.delete(f"/categories/{category_with_task_type.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot delete category: it has 1 task type(s). Delete them first."
    assert Category.objects.filter(id=category_with_task_type.id).exists()
