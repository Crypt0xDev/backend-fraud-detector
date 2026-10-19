import csv
import io

from conftest import ANALYST, CSV_HEADER, CSV_ROW, TRANSACTION

from config.settings import settings


def predict(client, headers, transactions=None, **params):
    return client.post(
        "/api/v1/predict",
        json={"transactions": transactions or [TRANSACTION]},
        headers=headers,
        params=params,
    )


def upload(client, headers, content: bytes, name: str = "lote.csv"):
    return client.post(
        "/api/v1/predict/batch",
        files={"file": (name, content, "text/csv")},
        headers=headers,
    )


def test_predecir_requiere_sesion(client):
    response = client.post("/api/v1/predict", json={"transactions": [TRANSACTION]})
    assert response.status_code == 401


def test_predecir_devuelve_score_y_guarda_historial(client, analyst):
    response = predict(client, analyst, explain="true")
    assert response.status_code == 200
    body = response.json()
    prediction = body["predictions"][0]
    assert 0 <= prediction["fraud_probability"] <= 1
    assert prediction["risk_level"] in ("low", "medium", "high")
    assert prediction["explanation"]
    assert body["model_version"] == "v001"
    assert body["threshold"] == body["risk_levels"]["high"]

    history = client.get("/api/v1/predictions", headers=analyst).json()
    assert history["total"] == 1
    assert history["items"][0]["username"] == ANALYST[0]
    assert history["items"][0]["name_orig"] == TRANSACTION["nameOrig"]


def test_historial_es_de_cada_usuario(client, admin, analyst, make_user):
    predict(client, analyst)
    other = make_user("otro")
    assert client.get("/api/v1/predictions", headers=other).json()["total"] == 0
    response = client.get("/api/v1/predictions?all=true", headers=other)
    assert response.status_code == 403
    everything = client.get("/api/v1/predictions?all=true", headers=admin).json()
    assert everything["total"] == 1


def test_valida_las_transacciones(client, analyst):
    bad = [
        {**TRANSACTION, "type": "OTRO"},
        {**TRANSACTION, "amount": -1},
        {key: value for key, value in TRANSACTION.items() if key != "amount"},
        {**TRANSACTION, "nameOrig": "C" * 101},
    ]
    for transaction in bad:
        assert predict(client, analyst, [transaction]).status_code == 422, transaction
    response = client.post(
        "/api/v1/predict", json={"transactions": []}, headers=analyst
    )
    assert response.status_code == 422


def test_rechaza_infinito_con_un_422_valido(client, analyst):
    # -Infinity ya daba 500 antes: el 422 no se podía convertir a JSON
    for field, value in (("amount", "Infinity"), ("oldbalanceOrg", "-Infinity")):
        fields = {
            "amount": "0",
            "oldbalanceOrg": "0",
            "newbalanceOrig": "0",
            "oldbalanceDest": "0",
            "newbalanceDest": "0",
            field: value,
        }
        numbers = ",".join(f'"{name}":{number}' for name, number in fields.items())
        body = f'{{"transactions":[{{"step":1,"type":"TRANSFER",{numbers}}}]}}'
        response = client.post(
            "/api/v1/predict",
            content=body,
            headers={**analyst, "Content-Type": "application/json"},
        )
        assert response.status_code == 422, field
        error = response.json()["detail"][0]
        assert error["loc"] == ["body", "transactions", 0, field]
        assert error["input"] in ("inf", "-inf")


def test_cuerpo_demasiado_grande_se_rechaza_antes_de_leerlo(client):
    limit = (settings.max_upload_mb + 1) * 1024 * 1024
    # Sin sesión: debe ser 413 y no 401, porque ni siquiera se lee el cuerpo
    response = client.post(
        "/api/v1/predict",
        content=b" " * (limit + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_cuerpo_grande_sin_content_length(client):
    limit = (settings.max_upload_mb + 1) * 1024 * 1024

    def chunks():
        sent = 0
        while sent <= limit:
            yield b" " * 1024 * 1024
            sent += 1024 * 1024

    response = client.post(
        "/api/v1/predict",
        content=chunks(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_csv_crea_un_lote_con_sus_archivos(client, analyst):
    content = f"{CSV_HEADER}\n{CSV_ROW}\n{CSV_ROW}\n".encode()
    response = upload(client, analyst, content)
    assert response.status_code == 200
    body = response.json()
    assert len(body["predictions"]) == 2
    assert body["batch_id"]

    page = client.get("/api/v1/batches", headers=analyst).json()
    assert page["total"] == 1
    assert page["items"][0]["total_rows"] == 2


def test_csv_escapa_formulas_en_el_resultado(client, analyst):
    row = CSV_ROW.replace("C1305486145", "=HYPERLINK(1)")
    response = upload(client, analyst, f"{CSV_HEADER}\n{row}\n".encode())
    batch_id = response.json()["batch_id"]
    link = client.get(
        f"/api/v1/batches/{batch_id}/files/predictions", headers=analyst
    ).json()["url"]
    downloaded = client.get(link.removeprefix("http://testserver"))
    assert downloaded.status_code == 200
    rows = list(csv.DictReader(io.StringIO(downloaded.text)))
    assert rows[0]["nameOrig"] == "'=HYPERLINK(1)"
    assert {"fraud_probability", "is_fraud", "risk_level"} <= set(rows[0])


def test_csv_no_valido(client, analyst, monkeypatch):
    assert upload(client, analyst, b"").status_code == 422
    assert upload(client, analyst, b"a,b\n1,2\n").status_code == 422
    assert upload(client, analyst, f"{CSV_HEADER}\n".encode()).status_code == 422

    monkeypatch.setattr(settings, "max_batch_rows", 2)
    many = f"{CSV_HEADER}\n{CSV_ROW}\n{CSV_ROW}\n{CSV_ROW}".encode()
    response = upload(client, analyst, many)
    assert response.status_code == 422
    assert "máximo de 2 filas" in response.json()["detail"]


def test_csv_supera_max_upload_mb(client, analyst, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    content = (CSV_HEADER + "\n").encode() + (CSV_ROW + "\n").encode() * 30_000
    assert len(content) > 1024 * 1024
    assert upload(client, analyst, content).status_code == 413


def test_limite_de_peticiones_por_usuario(client, analyst, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 2)
    assert predict(client, analyst).status_code == 200
    assert predict(client, analyst).status_code == 200
    assert predict(client, analyst).status_code == 429


def test_el_413_lleva_cabeceras_cors(client):
    origin = settings.cors_origins_list[0]
    limit = (settings.max_upload_mb + 1) * 1024 * 1024
    response = client.post(
        "/api/v1/predict",
        content=b" " * (limit + 1),
        headers={"Content-Type": "application/json", "Origin": origin},
    )
    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == origin
