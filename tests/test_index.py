import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize("path", ["/", "/api"])
def test_root_redirects_to_docs(client, path):
    response = client.get(path, follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_api_index(client):
    response = client.get("/api/v1")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Fraud Detector API",
        "version": "0.1.0",
        "docs": "http://testserver/docs",
        "health": "http://testserver/api/v1/health",
    }


def test_api_index_with_trailing_slash(client):
    assert client.get("/api/v1/").status_code == 200
