"""Adaptadores MediaPipe (CNN): landmarks faciales y segmentación capilar (REQ-02)."""
import threading
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from app.shared.errores import EntradaInvalida
from app.simulacion.domain.modelos import AnalisisFacial
from app.simulacion.domain.visagismo import clasificar_forma

HAIR_URL = "https://storage.googleapis.com/mediapipe-models/image_segmenter/hair_segmenter/float32/latest/hair_segmenter.tflite"
FACE_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"

# Los detectores de MediaPipe no son seguros entre hilos; FastAPI atiende peticiones en paralelo.
_lock = threading.Lock()


def _descargar(url: str, destino: Path) -> Path:
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"[LookFirst] Descargando {destino.name} ...")
    tmp = destino.with_suffix(destino.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(destino)
    return destino


def _mp_image(bgr: np.ndarray) -> mp.Image:
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))


class AnalizadorFacialMediaPipe:
    def __init__(self, models_dir: Path):
        ruta = _descargar(FACE_URL, models_dir / "face_landmarker.task")
        self._det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(ruta)),
            running_mode=vision.RunningMode.IMAGE, num_faces=1))

    def analizar(self, bgr: np.ndarray) -> tuple[AnalisisFacial, np.ndarray]:
        with _lock:
            res = self._det.detect(_mp_image(bgr))
        if not res.face_landmarks:
            raise EntradaInvalida("No se detectó ningún rostro. Mira de frente a la cámara con buena luz.")
        h, w = bgr.shape[:2]
        lm = res.face_landmarks[0]
        pts = np.array([[p.x * w, p.y * h] for p in lm])
        d = lambda a, b: float(np.linalg.norm(pts[a] - pts[b]))
        pomulos, mandibula, frente, alto = d(234, 454), d(172, 397), d(54, 284), d(10, 152)
        metricas = {"alto_ancho": round(alto / pomulos, 2), "mandibula_pomulos": round(mandibula / pomulos, 2),
                    "frente_pomulos": round(frente / pomulos, 2)}
        forma = clasificar_forma(metricas["alto_ancho"], metricas["mandibula_pomulos"])

        escudo = np.zeros((h, w), np.uint8)
        cv2.fillConvexPoly(escudo, cv2.convexHull(pts.astype(np.int32)), 255)
        escudo = cv2.erode(escudo, np.ones((9, 9), np.uint8))  # libera flequillo, entradas y patillas
        return AnalisisFacial(forma=forma, metricas=metricas), escudo


class SegmentadorCabelloMediaPipe:
    def __init__(self, models_dir: Path):
        ruta = _descargar(HAIR_URL, models_dir / "hair_segmenter.tflite")
        self._seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(ruta)),
            running_mode=vision.RunningMode.IMAGE, output_category_mask=True, output_confidence_masks=True))

    def segmentar(self, bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        with _lock:
            res = self._seg.segment(_mp_image(bgr))
            cat = res.category_mask.numpy_view().copy()
            confs = [c.numpy_view().copy() for c in (res.confidence_masks or [])]
        h, w = bgr.shape[:2]
        mask = (cat == 1).astype(np.uint8) * 255
        if mask.shape[:2] != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        if mask.mean() / 255 < 0.005:
            raise EntradaInvalida("No se detectó cabello en la imagen. Usa una foto donde se vea la cabeza completa.")
        conf = np.asarray(confs[1], np.float32) if len(confs) > 1 else mask.astype(np.float32) / 255
        if conf.shape[:2] != (h, w):
            conf = cv2.resize(conf, (w, h), interpolation=cv2.INTER_LINEAR)
        matte = cv2.GaussianBlur(np.clip(conf, 0, 1), (0, 0), 1.0)
        matte *= cv2.dilate(mask, np.ones((7, 7), np.uint8)) > 0
        return mask, matte
