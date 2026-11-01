from test_predictions import predict

POLICY = "/api/v1/model/policy"


def test_politica_por_defecto_es_la_del_entrenamiento(client, analyst):
    body = client.get(POLICY, headers=analyst).json()
    assert body["source"] == "metrics.json"
    assert body["high"] == body["default"]["high"]
    assert body["updated_by"] is None


def test_solo_con_permiso_de_editar_se_cambia(client, analyst):
    assert client.put(POLICY, json={"medium": 0.1, "high": 0.2}, headers=analyst).status_code == 403
    assert client.delete(POLICY, headers=analyst).status_code == 403


def test_medio_no_puede_superar_la_alerta(client, admin):
    response = client.put(POLICY, json={"medium": 0.8, "high": 0.5}, headers=admin)
    assert response.status_code == 422
    assert client.put(POLICY, json={"medium": 0, "high": 0}, headers=admin).status_code == 422


def test_el_umbral_nuevo_cambia_la_decision(client, admin, analyst):
    score = predict(client, analyst).json()["predictions"][0]["fraud_probability"]

    # Por encima del score: deja de ser alerta
    high = min(score + (1 - score) / 2, 1)
    if high > score:
        client.put(POLICY, json={"medium": high, "high": high}, headers=admin)
        result = predict(client, analyst).json()
        assert result["threshold"] == high
        assert result["predictions"][0]["is_fraud"] is False
        assert result["predictions"][0]["risk_level"] == "low"

    # Por debajo del score: es alerta
    low = score / 2
    response = client.put(POLICY, json={"medium": low / 2, "high": low}, headers=admin)
    assert response.status_code == 200
    assert response.json()["source"] == "web"
    assert response.json()["updated_by"] == "admin"
    result = predict(client, analyst).json()
    assert result["risk_levels"] == {"medium": low / 2, "high": low, "source": "web"}
    assert result["predictions"][0]["is_fraud"] is True

    info = client.get("/api/v1/model/info", headers=analyst).json()
    assert info["threshold"] == low
    history = client.get("/api/v1/predictions", headers=analyst).json()
    assert history["items"][0]["threshold"] == low


def test_restablecer_vuelve_al_entrenamiento(client, admin):
    default = client.get(POLICY, headers=admin).json()["default"]
    client.put(POLICY, json={"medium": 0.1, "high": 0.2}, headers=admin)
    body = client.delete(POLICY, headers=admin).json()
    assert body["source"] == "metrics.json"
    assert body["high"] == default["high"]
    assert client.delete(POLICY, headers=admin).status_code == 200
