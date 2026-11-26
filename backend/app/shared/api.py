"""Dependencias FastAPI compartidas: sesión de BD por petición (unidad de trabajo)."""
from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session


def get_db(request: Request) -> Iterator[Session]:
    db: Session = request.app.state.fabrica_sesiones()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_settings(request: Request):
    return request.app.state.settings
