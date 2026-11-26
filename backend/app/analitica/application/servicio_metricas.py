import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol

from app.analitica.domain.metricas import calcular
from app.shared.errores import EntradaInvalida


class LectorMetricas(Protocol):
    def filas(self, desde: datetime, hasta: datetime, estilista_id: uuid.UUID | None): ...


class ServicioMetricas:
    def __init__(self, lector: LectorMetricas, tiempo_tradicional_min: float):
        self.lector, self.tradicional = lector, tiempo_tradicional_min

    def resumen(self, desde: date, hasta: date, estilista_id: uuid.UUID | None) -> dict:
        if hasta < desde:
            raise EntradaInvalida("La fecha final debe ser posterior a la inicial.")
        # Fechas locales de Lima (UTC-5) convertidas a UTC
        lima = timezone(timedelta(hours=-5))
        d = datetime.combine(desde, time.min, lima).astimezone(timezone.utc)
        h = datetime.combine(hasta + timedelta(days=1), time.min, lima).astimezone(timezone.utc)
        consultas, sims = self.lector.filas(d, h, estilista_id)
        return {"desde": desde.isoformat(), "hasta": hasta.isoformat(), **calcular(consultas, sims, self.tradicional)}
