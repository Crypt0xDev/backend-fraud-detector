import io
from urllib.parse import urlsplit

import pandas as pd
import pytest

import main
from tests.factories import make_transaction
from utils.storage import LocalStorage, StorageError, open_storage
from utils.token import create_download_token, create_token

DOWNLOAD_URL = "http://api.test/api/v1/batches/download"


def local_storage(tmp_path, backend="local", **overrides):
    options = {
        "local_dir": tmp_path,
        "download_url": DOWNLOAD_URL,
        "supabase_url": None,
        "supabase_secret_key": None,
        "bucket": "batches",
    }
    return open_storage(backend, **(options | overrides))


def test_open_storage_local_creates_folder(tmp_path):
    storage = local_storage(tmp_path)

    assert isinstance(storage, LocalStorage)
    assert (tmp_path / "batches").is_dir()


def test_open_storage_without_backend_or_supabase(tmp_path):
    assert local_storage(tmp_path, backend=None) is None


def test_open_storage_supabase_without_keys(tmp_path):
    assert local_storage(tmp_path, backend="supabase") is None


def test_upload_and_delete(tmp_path):
    storage = local_storage(tmp_path)

    storage.upload("lote/input.csv", b"a,b\n1,2\n", "text/csv")
    assert (tmp_path / "batches" / "lote" / "input.csv").read_bytes() == b"a,b\n1,2\n"

    storage.delete(["lote/input.csv"])
    assert not (tmp_path / "batches" / "lote").exists()


def test_upload_never_overwrites(tmp_path):
    storage = local_storage(tmp_path)
    storage.upload("lote/input.csv", b"original", "text/csv")

    with pytest.raises(StorageError):
        storage.upload("lote/input.csv", b"otro", "text/csv")
    assert (tmp_path / "batches" / "lote" / "input.csv").read_bytes() == b"original"


def test_rejects_paths_outside_root(tmp_path):
    storage = local_storage(tmp_path)

    with pytest.raises(StorageError):
        storage.upload("../fuera.csv", b"x", "text/csv")
    assert not (tmp_path / "fuera.csv").exists()


def test_signed_url_points_to_api(tmp_path):
    storage = local_storage(tmp_path)
    storage.upload("lote/input.csv", b"x", "text/csv")

    url = storage.signed_url("lote/input.csv", 300, "pagos.csv")

    assert url.startswith(f"{DOWNLOAD_URL}?token=")


@pytest.fixture
def client(client_with_model_path, pipeline_path, tmp_path, monkeypatch):
    storage = local_storage(tmp_path)
    monkeypatch.setattr(main, "open_storage", lambda *_args, **_kwargs: storage)
    with client_with_model_path(pipeline_path) as client:
        yield client


def upload(client):
    content = pd.DataFrame([make_transaction(isFraud=1), make_transaction()])
    return client.post(
        "/api/v1/predict/csv",
        files={"file": ("pagos.csv", content.to_csv(index=False).encode(), "text/csv")},
    )


def download_path(url):
    parts = urlsplit(url)
    return f"{parts.path}?{parts.query}"


def test_csv_is_saved_and_downloadable(client):
    batch_id = upload(client).json()["batch_id"]
    assert batch_id is not None

    url = client.get(f"/api/v1/batches/{batch_id}/files/predictions").json()["url"]
    response = client.get(download_path(url))

    assert response.status_code == 200
    assert "pagos_predicciones.csv" in response.headers["content-disposition"]
    saved = pd.read_csv(io.BytesIO(response.content))
    assert {"fraud_probability", "is_fraud"} <= set(saved.columns)


def test_download_rejects_invalid_token(client):
    response = client.get("/api/v1/batches/download", params={"token": "x"})

    assert response.status_code == 403


def test_download_rejects_session_token(client):
    session_token, _ = create_token("tester")

    response = client.get("/api/v1/batches/download", params={"token": session_token})

    assert response.status_code == 403


def test_download_rejects_expired_token(client):
    batch_id = upload(client).json()["batch_id"]
    token = create_download_token(f"{batch_id}/input.csv", "pagos.csv", -1)

    response = client.get("/api/v1/batches/download", params={"token": token})

    assert response.status_code == 403


def test_download_after_delete(client):
    batch_id = upload(client).json()["batch_id"]
    url = client.get(f"/api/v1/batches/{batch_id}/files/input").json()["url"]

    assert client.delete(f"/api/v1/batches/{batch_id}").status_code == 204
    assert client.get(download_path(url)).status_code == 404


def test_download_not_available_with_other_storage(
    client_with_model_path, pipeline_path
):
    token = create_download_token("lote/input.csv", "pagos.csv", 300)

    with client_with_model_path(pipeline_path) as client:
        response = client.get("/api/v1/batches/download", params={"token": token})

    assert response.status_code == 404
