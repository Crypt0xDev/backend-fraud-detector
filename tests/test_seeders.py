import pytest

from config.settings import settings
from seeders.admin_seeder import seed_admin
from tests.factories import InMemoryUserRepository
from utils.password import hash_password, verify_password


@pytest.fixture
def admin_env(monkeypatch):
    monkeypatch.setattr(settings, "admin_username", "admin")
    monkeypatch.setattr(settings, "admin_password", "secreta123")


def test_seed_admin_creates_user(admin_env):
    users = InMemoryUserRepository()

    seed_admin(users)

    assert verify_password("secreta123", users.get_password_hash("admin"))


def test_seed_admin_keeps_existing_password(admin_env):
    users = InMemoryUserRepository()
    users.save("admin", hash_password("otra-clave"))

    seed_admin(users)

    assert verify_password("otra-clave", users.get_password_hash("admin"))


def test_seed_admin_without_env(monkeypatch):
    monkeypatch.setattr(settings, "admin_username", None)
    users = InMemoryUserRepository()

    seed_admin(users)

    assert users.users == {}


def test_seed_admin_rejects_short_password(admin_env, monkeypatch):
    monkeypatch.setattr(settings, "admin_password", "corta")
    users = InMemoryUserRepository()

    seed_admin(users)

    assert users.users == {}


def test_admin_is_seeded_on_startup(admin_env, client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path, authenticated=False) as client:
        response = client.post(
            "/api/v1/auth/login", data={"username": "admin", "password": "secreta123"}
        )

    assert response.status_code == 200
