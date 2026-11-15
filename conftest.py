from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from roadmap.models import Category, TaskType


@pytest.fixture
def api_client():
    """Клієнт без токена — неавторизований користувач."""
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", email="alice@example.com", password="Str0ng-Pass!")


@pytest.fixture
def auth_client(user):
    """Клієнт із валідним access токеном користувача."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


@pytest.fixture
def expired_token_client(user):
    """Клієнт із простроченим access токеном."""
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=-timedelta(seconds=1))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Web", description="Вразливості вебзастосунків")


@pytest.fixture
def category_with_task_type(category):
    """Категорія, до якої прив'язаний тип завдання: видалити її не можна."""
    TaskType.objects.create(category=category, name="SQL Injection")
    return category
