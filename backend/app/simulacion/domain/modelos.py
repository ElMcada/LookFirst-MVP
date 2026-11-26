from dataclasses import dataclass
from enum import Enum

import numpy as np

from app.shared.kernel import FormaRostro, TipoCorte


class FuentePrompt(str, Enum):
    CATALOGO = "catalogo"
    LLM = "llm"
    PALABRAS_CLAVE = "palabras_clave"


class ModoSimulacion(str, Enum):
    IA_GENERATIVA = "ia_generativa"    # inpainting en GPU (Colab)
    RESPALDO_LOCAL = "respaldo_local"  # recoloreado OpenCV, solo color


@dataclass(frozen=True)
class AnalisisFacial:
    forma: FormaRostro
    metricas: dict[str, float]


@dataclass(frozen=True)
class EspecificacionLook:
    """Qué look se quiere, ya traducido a términos técnicos."""
    prompt_en: str
    tipo_corte: TipoCorte
    fuente: FuentePrompt
    color_hex: str | None = None
    degradado: bool = False


@dataclass
class FotoPreparada:
    """Foto del cliente ya analizada. Vive SOLO en memoria durante la consulta (REQ-09)."""
    bgr: np.ndarray
    mascara: np.ndarray      # cabello binario 0/255
    matte: np.ndarray        # cabello suave 0..1 (bordes finos)
    escudo: np.ndarray       # facciones protegidas 0/255 (ojos, nariz, boca)
    analisis: AnalisisFacial


@dataclass(frozen=True)
class ResultadoLook:
    imagen_jpg: bytes
    modo: ModoSimulacion
    aviso: str | None
