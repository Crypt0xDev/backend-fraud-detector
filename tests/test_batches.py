import pytest
from conftest import CSV_HEADER, CSV_ROW

from utils.token import create_download_token


@pytest.fixture
def batch_id(client, analyst) -> str:
    response = client.post(
        "/api/v1/predict/batch",
        files={
            "file": ("mis datos.csv", f"{CSV_HEADER}\n{CSV_ROW}\n".encode(), "text/csv")
        },
        headers=analyst,
    )
    assert response.status_code == 200
    return response.json()["batch_id"]


def test_otro_usuario_no_ve_ni_borra_el_lote(client, batch_id, make_user):
    other = make_user("otro")
    assert client.get("/api/v1/batches", headers=other).json()["total"] == 0
    url = f"/api/v1/batches/{batch_id}"
    assert client.get(f"{url}/files/input", headers=other).status_code == 404
    assert client.delete(url, headers=other).status_code == 404
    assert client.get("/api/v1/batches?all=true", headers=other).status_code == 403


def test_el_root_ve_todos_los_lotes(client, admin, batch_id):
    assert client.get("/api/v1/batches", headers=admin).json()["total"] == 0
    page = client.get("/api/v1/batches?all=true", headers=admin).json()
    assert [item["id"] for item in page["items"]] == [batch_id]


def test_descargar_el_csv_original(client, analyst, batch_id):
    response = client.get(f"/api/v1/batches/{batch_id}/files/input", headers=analyst)
    assert response.status_code == 200
    assert response.json()["expires_in"] == 300
    downloaded = client.get(response.json()["url"].removeprefix("http://testserver"))
    assert downloaded.status_code == 200
    assert downloaded.text.startswith(CSV_HEADER)
    # Starlette usa filename* (RFC 5987) porque el nombre tiene un espacio
    disposition = downloaded.headers["content-disposition"]
    assert disposition == "attachment; filename*=utf-8''mis%20datos.csv"


def test_token_de_descarga_alterado_o_fuera_de_la_carpeta(client, analyst, batch_id):
    assert client.get("/api/v1/batches/download?token=falso").status_code == 403
    escape = create_download_token("../../../etc/passwd", "x.csv", 60)
    assert client.get(f"/api/v1/batches/download?token={escape}").status_code == 404


def test_borrar_lote_borra_los_archivos(client, analyst, batch_id, tmp_path):
    folder = tmp_path / "batches" / batch_id
    assert folder.is_dir()
    assert (
        client.delete(f"/api/v1/batches/{batch_id}", headers=analyst).status_code == 204
    )
    assert not folder.exists()
    assert (
        client.delete(f"/api/v1/batches/{batch_id}", headers=analyst).status_code == 404
    )


def test_estadisticas(client, analyst, batch_id):
    stats = client.get("/api/v1/batches/stats?days=7&tz=America/Lima", headers=analyst)
    assert stats.status_code == 200
    body = stats.json()
    assert body["batches"] == 1
    assert len(body["days"]) == 7
    assert sum(day["batches"] for day in body["days"]) == 1
    response = client.get("/api/v1/batches/stats?tz=../../etc", headers=analyst)
    assert response.status_code == 422


def test_paginacion(client, analyst, batch_id):
    page = client.get("/api/v1/batches?page=2&page_size=1", headers=analyst).json()
    assert page["items"] == [] and page["total"] == 1
    assert (
        client.get("/api/v1/batches?page_size=101", headers=analyst).status_code == 422
    )
