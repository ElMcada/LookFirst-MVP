import re
import uuid
from dataclasses import dataclass, field
from enum import Enum

from app.shared.errores import EntradaInvalida
from app.shared.kernel import FormaRostro, TipoCorte

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
CODIGO_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class TipoServicio(str, Enum):
    CORTE = "corte"
    TINTE = "tinte"


@dataclass
class Estilo:
    """Servicio que el salón realmente ofrece (REQ-10). Solo estos se recomiendan."""
    codigo: str
    nombre: str
    tipo: TipoServicio
    descripcion: str
    prompt_en: str
    tipo_corte: TipoCorte
    formas: set[FormaRostro]
    color_hex: str | None = None
    degradado: bool = False
    activo: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        self.codigo = (self.codigo or "").strip().lower()
        self.nombre = (self.nombre or "").strip()
        self.prompt_en = (self.prompt_en or "").strip()
        self.color_hex = self.color_hex.upper() if self.color_hex else None
        self.formas = set(self.formas)
        if not CODIGO_RE.match(self.codigo):
            raise EntradaInvalida("El código debe ser en minúsculas con guiones bajos, p. ej. bob_capas.")
        if not 2 <= len(self.nombre) <= 80:
            raise EntradaInvalida("El nombre debe tener entre 2 y 80 caracteres.")
        if not 10 <= len(self.prompt_en) <= 400:
            raise EntradaInvalida("El prompt técnico debe tener entre 10 y 400 caracteres.")
        if self.color_hex and not HEX_RE.match(self.color_hex):
            raise EntradaInvalida("El color debe tener formato #RRGGBB.")
        if not self.formas:
            raise EntradaInvalida("Indica al menos una forma de rostro recomendada.")
        if self.tipo == TipoServicio.TINTE:
            if self.tipo_corte != TipoCorte.CONSERVAR:
                raise EntradaInvalida("Un tinte no cambia la silueta: su tipo de corte debe ser 'conservar'.")
            if not self.color_hex:
                raise EntradaInvalida("Un tinte necesita un color objetivo.")
        elif self.tipo_corte == TipoCorte.CONSERVAR:
            raise EntradaInvalida("Un corte debe indicar el largo resultante (calvo, corto, medio o largo).")

    def recomendable_para(self, forma: FormaRostro) -> bool:
        return self.activo and forma in self.formas
