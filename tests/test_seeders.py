import pytest

from config.settings import settings
from seeders.admin_seeder import seed_admin
from seeders.user_seeder import seed_user
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


def test_seed_admin_has_admin_role(admin_env):
    users = InMemoryUserRepository()

    seed_admin(users)

    assert users.get_role("admin") == "admin"


def test_seed_admin_promotes_existing_user_without_touching_password(admin_env):
    users = InMemoryUserRepository()
    users.save("admin", hash_password("otra-clave"))

    seed_admin(users)

    assert users.get_role("admin") == "admin"
    assert verify_password("otra-clave", users.get_password_hash("admin"))


@pytest.fixture
def user_env(monkeypatch):
    monkeypatch.setattr(settings, "user_username", "usuario")
    monkeypatch.setattr(settings, "user_password", "normal1234")


def test_seed_user_creates_normal_user(user_env):
    users = InMemoryUserRepository()

    seed_user(users)

    assert users.get_role("usuario") == "user"
    assert verify_password("normal1234", users.get_password_hash("usuario"))


def test_seed_user_without_env(monkeypatch):
    monkeypatch.setattr(settings, "user_username", None)
    users = InMemoryUserRepository()

    seed_user(users)

    assert users.users == {}


def test_both_users_seeded_on_startup(
    admin_env, user_env, client_with_model_path, pipeline_path
):
    with client_with_model_path(pipeline_path, authenticated=False) as client:
        roles = {}
        for username, password in [("admin", "secreta123"), ("usuario", "normal1234")]:
            token = client.post(
                "/api/v1/auth/login",
                data={"username": username, "password": password},
            ).json()["access_token"]
            me = client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            roles[username] = me.json()["role"]

    assert roles == {"admin": "admin", "usuario": "user"}
