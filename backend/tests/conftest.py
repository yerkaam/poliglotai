import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from users.models import User

PASSWORD = "englishday1"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="aigerim@mail.kz", password=PASSWORD, name="Айгерім")


@pytest.fixture
def client(user):
    api = APIClient()
    response = api.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
    assert response.status_code == 200
    return api


@pytest.fixture
def anon():
    return APIClient()
