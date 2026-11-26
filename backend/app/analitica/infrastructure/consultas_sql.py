"""Modelo de lectura: consulta las tablas de Consulta y Catálogo sin modificarlas."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analitica.domain.metricas import FilaConsulta, FilaSimulacion
from app.catalogo.infrastructure.orm import EstiloORM
from app.consulta.infrastructure.orm import ConsultaORM, SimulacionORM
from app.shared.kernel import a_utc


class LectorMetricasSQL:
    def __init__(self, db: Session):
        self.db = db

    def filas(self, desde: datetime, hasta: datetime, estilista_id: uuid.UUID | None):
        filtro = [ConsultaORM.iniciada_en >= desde, ConsultaORM.iniciada_en < hasta]
        if estilista_id:
            filtro.append(ConsultaORM.estilista_id == estilista_id)

        consultas = [FilaConsulta(id=r.id, estado=r.estado.value, iniciada_en=a_utc(r.iniciada_en),
                                  finalizada_en=a_utc(r.finalizada_en), satisfaccion=r.satisfaccion)
                     for r in self.db.execute(select(ConsultaORM.id, ConsultaORM.estado, ConsultaORM.iniciada_en,
                                                     ConsultaORM.finalizada_en, ConsultaORM.satisfaccion).where(*filtro))]

        q = (select(SimulacionORM.consulta_id, SimulacionORM.origen, SimulacionORM.modo, SimulacionORM.latencia_ms,
                    EstiloORM.nombre, SimulacionORM.instruccion, SimulacionORM.elegida_en)
             .join(ConsultaORM, ConsultaORM.id == SimulacionORM.consulta_id)
             .outerjoin(EstiloORM, EstiloORM.id == SimulacionORM.estilo_id)
             .where(*filtro))
        sims = [FilaSimulacion(consulta_id=r[0], origen=r[1].value, modo=r[2].value, latencia_ms=r[3],
                               estilo_nombre=r[4], instruccion=r[5], elegida_en=a_utc(r[6]))
                for r in self.db.execute(q)]
        return consultas, sims
