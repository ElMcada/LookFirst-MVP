import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.analitica.application.servicio_metricas import ServicioMetricas
from app.analitica.infrastructure.consultas_sql import LectorMetricasSQL
from app.iam.api.dependencias import usuario_actual
from app.iam.domain.usuario import Usuario
from app.shared.api import get_db

router = APIRouter(prefix="/metricas", tags=["Analítica"])


@router.get("")
def resumen(request: Request, desde: date | None = None, hasta: date | None = None,
            estilista_id: uuid.UUID | None = None, u: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    hasta = hasta or date.today()
    desde = desde or hasta - timedelta(days=30)
    # El estilista solo ve sus propias consultas; el administrador ve todas o filtra por estilista.
    filtro = estilista_id if u.es_admin else u.id
    svc = ServicioMetricas(LectorMetricasSQL(db), request.app.state.settings.tiempo_decision_tradicional_min)
    return svc.resumen(desde, hasta, filtro)
