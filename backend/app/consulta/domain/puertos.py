import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from app.consulta.domain.consulta import Consulta
from app.shared.kernel import FormaRostro, TipoCorte


class RepositorioConsultas(Protocol):
    def por_id(self, consulta_id: uuid.UUID) -> Consulta | None: ...
    def guardar(self, consulta: Consulta) -> None: ...
    def activas(self, iniciadas_antes_de: datetime | None = None) -> list[Consulta]: ...


class AlmacenFotosTemporal(Protocol):
    """Guarda la foto analizada SOLO en memoria mientras dura la consulta."""
    def guardar(self, consulta_id: uuid.UUID, foto: Any) -> None: ...
    def obtener(self, consulta_id: uuid.UUID) -> Any | None: ...
    def eliminar(self, consulta_id: uuid.UUID) -> bool: ...
    def vencidas(self, ttl_s: float) -> list[uuid.UUID]: ...


@dataclass(frozen=True)
class EstiloOfrecido:
    """Lo que la Consulta necesita saber de un estilo del Catálogo (capa anticorrupción)."""
    id: uuid.UUID
    nombre: str
    prompt_en: str
    tipo_corte: TipoCorte
    color_hex: str | None
    degradado: bool


class ProveedorEstilos(Protocol):
    def obtener(self, estilo_id: uuid.UUID) -> EstiloOfrecido: ...
    def recomendar(self, forma: FormaRostro) -> tuple[str, list[dict]]: ...
