"""Fotos en memoria RAM: nunca tocan el disco ni la base de datos (REQ-09, Ley N.° 29733)."""
import threading
import time
import uuid
from typing import Any


class AlmacenFotosMemoria:
    def __init__(self):
        self._fotos: dict[uuid.UUID, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def guardar(self, consulta_id: uuid.UUID, foto: Any) -> None:
        with self._lock:
            self._fotos[consulta_id] = (time.monotonic(), foto)

    def obtener(self, consulta_id: uuid.UUID) -> Any | None:
        with self._lock:
            item = self._fotos.get(consulta_id)
        return item[1] if item else None

    def eliminar(self, consulta_id: uuid.UUID) -> bool:
        with self._lock:
            return self._fotos.pop(consulta_id, None) is not None

    def vencidas(self, ttl_s: float) -> list[uuid.UUID]:
        limite = time.monotonic() - ttl_s
        with self._lock:
            return [cid for cid, (t, _) in self._fotos.items() if t < limite]

    def __len__(self) -> int:
        with self._lock:
            return len(self._fotos)
