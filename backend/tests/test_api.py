"""Pruebas de integración del flujo completo de una consulta (con visión simulada y BD SQLite en memoria)."""
from app.consulta.domain.consulta import VERSION_CONSENTIMIENTO
from tests.conftest import foto_jpg, token

CONSENT = {"acepta_consentimiento": True, "version_consentimiento": VERSION_CONSENTIMIENTO}


def _consulta_con_foto(client, h):
    cid = client.post("/consultas", headers=h, json=CONSENT).json()["id"]
    r = client.post(f"/consultas/{cid}/foto", headers=h, files={"file": ("f.jpg", foto_jpg(), "image/jpeg")})
    assert r.status_code == 200, r.text
    return cid, r.json()


def test_requiere_login(client):
    assert client.get("/estilos").status_code == 401
    assert client.post("/auth/login", json={"email": "admin@salon.pe", "password": "mala"}).status_code == 401


def test_flujo_completo_de_consulta(client, estilista):
    assert client.post("/consultas", headers=estilista,
                       json={**CONSENT, "acepta_consentimiento": False}).status_code == 422

    cid, analisis = _consulta_con_foto(client, estilista)
    assert analisis["forma_rostro"] == "ovalado"
    assert analisis["recomendaciones"] and all("ovalado" in e["formas"] for e in analisis["recomendaciones"])

    tinte = next(e for e in analisis["recomendaciones"] if e["tipo"] == "tinte")
    r1 = client.post(f"/consultas/{cid}/simulaciones", headers=estilista,
                     json={"origen": "catalogo", "estilo_id": tinte["id"]})
    assert r1.status_code == 201, r1.text
    assert r1.json()["tipo_corte"] == "conservar" and r1.json()["modo"] == "respaldo_local" and r1.json()["imagen_b64"]

    r2 = client.post(f"/consultas/{cid}/simulaciones", headers=estilista,
                     json={"origen": "voz", "instruccion": "quiero un bob cobrizo"})
    assert r2.status_code == 201 and r2.json()["tipo_corte"] == "medio"
    assert r2.json()["aviso"]  # sin Colab no puede cambiar el corte: debe avisarlo

    assert client.post(f"/consultas/{cid}/simulaciones", headers=estilista,
                       json={"origen": "texto", "instruccion": "hola"}).status_code == 422

    assert client.post(f"/consultas/{cid}/simulaciones/{r2.json()['id']}/elegir", headers=estilista).status_code == 200
    fin = client.post(f"/consultas/{cid}/finalizar", headers=estilista, json={"satisfaccion": 9})
    assert fin.status_code == 200 and fin.json()["datos_eliminados_en"]
    assert client.app.state.fotos.obtener(__import__("uuid").UUID(cid)) is None

    assert client.post(f"/consultas/{cid}/simulaciones", headers=estilista,
                       json={"origen": "texto", "instruccion": "rubio"}).status_code == 409

    m = client.get("/metricas", headers=estilista).json()
    assert m["consultas"]["finalizadas"] == 1 and m["satisfaccion"]["promedio"] == 9
    assert m["latencia"]["simulaciones"] == 2 and m["simulaciones"]["por_origen"] == {"catalogo": 1, "voz": 1}


def test_otro_estilista_no_accede_a_la_consulta(client, admin, estilista):
    cid, _ = _consulta_con_foto(client, estilista)
    client.post("/usuarios", headers=admin, json={"nombre": "Luis", "email": "luis@salon.pe", "password": "estilista2"})
    otro = token(client, "luis@salon.pe", "estilista2")
    assert client.post(f"/consultas/{cid}/finalizar", headers=otro, json={}).status_code == 403


def test_revocar_consentimiento_borra_foto(client, estilista):
    cid, _ = _consulta_con_foto(client, estilista)
    r = client.post(f"/consultas/{cid}/revocar", headers=estilista)
    assert r.json()["estado"] == "cancelada" and len(client.app.state.fotos) == 0


def test_purga_automatica_por_ttl(client, estilista):
    from app.bootstrap import _servicio_consulta
    cid, _ = _consulta_con_foto(client, estilista)
    with client.app.state.fabrica_sesiones.begin() as db:
        assert _servicio_consulta(client.app, db).expirar_vencidas(ttl_s=-1) == 1
    assert len(client.app.state.fotos) == 0
    assert client.post(f"/consultas/{cid}/finalizar", headers=estilista, json={}).status_code == 409


def test_catalogo_solo_admin_y_validaciones(client, admin, estilista):
    nuevo = {"codigo": "mullet_moderno", "nombre": "Mullet moderno", "tipo": "corte", "prompt_en": "modern textured mullet haircut",
             "tipo_corte": "corto", "formas": ["ovalado"]}
    assert client.post("/estilos", headers=estilista, json=nuevo).status_code == 403
    r = client.post("/estilos", headers=admin, json=nuevo)
    assert r.status_code == 201
    assert client.post("/estilos", headers=admin, json=nuevo).status_code == 409
    assert client.post("/estilos", headers=admin, json={**nuevo, "codigo": "x_y", "tipo": "tinte"}).status_code == 422
    eid = r.json()["id"]
    assert client.patch(f"/estilos/{eid}", headers=admin, json={"activo": False}).json()["activo"] is False
    assert all(e["id"] != eid for e in client.get("/estilos", headers=estilista).json())


def test_admin_no_se_desactiva_a_si_mismo(client, admin):
    yo = client.get("/auth/me", headers=admin).json()
    assert client.patch(f"/usuarios/{yo['id']}", headers=admin, json={"activo": False}).status_code == 409
