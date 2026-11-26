import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.bootstrap import create_app
from app.shared.config import BACKEND_DIR, Settings
from app.shared.kernel import FormaRostro
from app.simulacion.application.motor import MotorSimulacion
from app.simulacion.domain.modelos import AnalisisFacial
from app.simulacion.infrastructure.interprete_palabras_clave import InterpretePalabrasClave

ADMIN = {"email": "admin@salon.pe", "password": "admin12345"}


class AnalizadorFalso:
    def analizar(self, bgr):
        h, w = bgr.shape[:2]
        escudo = np.zeros((h, w), np.uint8)
        cv2.ellipse(escudo, (w // 2, int(h * 0.55)), (w // 6, h // 5), 0, 0, 360, 255, -1)
        return AnalisisFacial(FormaRostro.OVALADO, {"alto_ancho": 1.3, "mandibula_pomulos": 0.8, "frente_pomulos": 0.9}), escudo


class SegmentadorFalso:
    def segmentar(self, bgr):
        h, w = bgr.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        cv2.ellipse(mask, (w // 2, int(h * 0.35)), (w // 4, h // 4), 0, 180, 360, 255, -1)
        return mask, mask.astype(np.float32) / 255


class InpainterApagado:
    disponible = False

    def generar(self, *a, **k):
        return None


def motor_falso() -> MotorSimulacion:
    return MotorSimulacion(AnalizadorFalso(), SegmentadorFalso(), InpainterApagado(), InterpretePalabrasClave())


def foto_jpg() -> bytes:
    img = np.full((480, 360, 3), 180, np.uint8)
    cv2.rectangle(img, (90, 40), (270, 200), (30, 25, 20), -1)
    return cv2.imencode(".jpg", img)[1].tobytes()


@pytest.fixture
def client():
    s = Settings(database_url="sqlite://", jwt_secret="secreto-de-prueba-con-longitud-suficiente-32b", admin_email=ADMIN["email"],
                 admin_password=ADMIN["password"], colab_url="", groq_api_key="", gemini_api_key="",
                 catalogo_semilla=BACKEND_DIR / "catalogo_salon.json")
    with TestClient(create_app(s, motor=motor_falso())) as c:
        yield c


def token(client, email, password) -> dict:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def admin(client):
    return token(client, **ADMIN)


@pytest.fixture
def estilista(client, admin):
    r = client.post("/usuarios", headers=admin, json={"nombre": "Ana Estilista", "email": "ana@salon.pe",
                                                      "password": "estilista1", "rol": "estilista"})
    assert r.status_code == 201, r.text
    return token(client, "ana@salon.pe", "estilista1")
