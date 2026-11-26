from typing import Protocol

import numpy as np

from app.simulacion.domain.modelos import AnalisisFacial, EspecificacionLook


class AnalizadorFacial(Protocol):
    def analizar(self, bgr: np.ndarray) -> tuple[AnalisisFacial, np.ndarray]:
        """Devuelve el análisis y el escudo de facciones. Lanza EntradaInvalida si no hay rostro."""
        ...


class SegmentadorCabello(Protocol):
    def segmentar(self, bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Devuelve (máscara binaria 0/255, matte suave 0..1)."""
        ...


class InterpreteInstrucciones(Protocol):
    def interpretar(self, texto: str) -> EspecificacionLook | None: ...


class Inpainter(Protocol):
    @property
    def disponible(self) -> bool: ...

    def generar(self, bgr: np.ndarray, mascara: np.ndarray, prompt: str, negativo: str,
                timeout_s: float) -> np.ndarray | None:
        """Imagen generada del mismo tamaño, o None si falla o no llega a tiempo."""
        ...
