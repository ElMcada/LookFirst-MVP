"""Kernel compartido: conceptos que varios bounded contexts usan con el mismo significado."""
from datetime import datetime, timezone
from enum import Enum


class FormaRostro(str, Enum):
    OVALADO = "ovalado"
    REDONDO = "redondo"
    CUADRADO = "cuadrado"
    ALARGADO = "alargado"


class TipoCorte(str, Enum):
    """Cuánto cambia la silueta del cabello. 'conservar' = solo color (tintes)."""
    CONSERVAR = "conservar"
    CALVO = "calvo"
    CORTO = "corto"
    MEDIO = "medio"
    LARGO = "largo"


def ahora() -> datetime:
    return datetime.now(timezone.utc)


def a_utc(dt: datetime | None) -> datetime | None:
    """SQLite devuelve fechas sin zona horaria; PostgreSQL (timestamptz) sí. Normaliza ambas."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
