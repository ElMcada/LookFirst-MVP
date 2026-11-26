"""Adaptador del servidor de inpainting en Google Colab (GPU T4) expuesto con un túnel de Cloudflare."""
import cv2
import numpy as np
import requests


class InpainterColab:
    def __init__(self, url: str, pasos: int = 18):
        self.url, self.pasos = url.rstrip("/"), pasos
        self._http = requests.Session()  # reutiliza la conexión TLS: ahorra ~0.3 s por simulación

    @property
    def disponible(self) -> bool:
        return bool(self.url)

    def generar(self, bgr: np.ndarray, mascara: np.ndarray, prompt: str, negativo: str,
                timeout_s: float) -> np.ndarray | None:
        if not self.disponible:
            return None
        try:
            img = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes()
            msk = cv2.imencode(".png", mascara)[1].tobytes()
            r = self._http.post(f"{self.url}/inpaint", timeout=timeout_s,
                                files={"image": ("img.jpg", img, "image/jpeg"), "mask": ("mask.png", msk, "image/png")},
                                data={"prompt": prompt, "negative_prompt": negativo, "steps": str(self.pasos)})
            if r.status_code != 200:
                print("[Colab] HTTP", r.status_code, r.text[:150])
                return None
            out = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
            return None if out is None else cv2.resize(out, (bgr.shape[1], bgr.shape[0]))
        except requests.RequestException as e:
            print("[Colab] sin respuesta a tiempo:", type(e).__name__)
            return None
