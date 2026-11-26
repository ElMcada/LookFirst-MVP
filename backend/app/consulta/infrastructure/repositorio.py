import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consulta.domain.consulta import Consulta, EstadoConsulta, Simulacion
from app.consulta.infrastructure.orm import ConsultaORM, SimulacionORM
from app.shared.kernel import a_utc
from app.simulacion.domain.modelos import FuentePrompt, ModoSimulacion


def _sim_dominio(f: SimulacionORM) -> Simulacion:
    return Simulacion(id=f.id, consulta_id=f.consulta_id, origen=f.origen, tipo_corte=f.tipo_corte,
                      fuente_prompt=f.fuente_prompt.value, modo=f.modo.value, latencia_ms=f.latencia_ms,
                      estilo_id=f.estilo_id, instruccion=f.instruccion, elegida_en=a_utc(f.elegida_en),
                      creada_en=a_utc(f.creada_en))


def _a_dominio(f: ConsultaORM) -> Consulta:
    return Consulta(id=f.id, estilista_id=f.estilista_id, consentimiento_version=f.consentimiento_version,
                    consentimiento_otorgado_en=a_utc(f.consentimiento_otorgado_en), estado=f.estado,
                    iniciada_en=a_utc(f.iniciada_en), finalizada_en=a_utc(f.finalizada_en),
                    datos_eliminados_en=a_utc(f.datos_eliminados_en), satisfaccion=f.satisfaccion,
                    simulaciones=[_sim_dominio(s) for s in f.simulaciones])


class RepositorioConsultasSQL:
    def __init__(self, db: Session):
        self.db = db

    def por_id(self, consulta_id: uuid.UUID) -> Consulta | None:
        fila = self.db.get(ConsultaORM, consulta_id)
        return _a_dominio(fila) if fila else None

    def activas(self, iniciadas_antes_de: datetime | None = None) -> list[Consulta]:
        q = select(ConsultaORM).where(ConsultaORM.estado == EstadoConsulta.ACTIVA)
        if iniciadas_antes_de:
            q = q.where(ConsultaORM.iniciada_en < iniciadas_antes_de)
        return [_a_dominio(f) for f in self.db.scalars(q)]

    def guardar(self, c: Consulta) -> None:
        fila = self.db.get(ConsultaORM, c.id)
        if fila is None:
            fila = ConsultaORM(id=c.id, estilista_id=c.estilista_id, consentimiento_version=c.consentimiento_version,
                               consentimiento_otorgado_en=c.consentimiento_otorgado_en, iniciada_en=c.iniciada_en)
            self.db.add(fila)
        fila.estado, fila.finalizada_en = c.estado, c.finalizada_en
        fila.datos_eliminados_en, fila.satisfaccion = c.datos_eliminados_en, c.satisfaccion

        existentes = {s.id: s for s in fila.simulaciones}
        # 1) primero se quitan las marcas de "elegida" (el índice único parcial no admite dos a la vez)
        for s in c.simulaciones:
            if s.id in existentes and s.elegida_en is None:
                existentes[s.id].elegida_en = None
        self.db.flush()
        # 2) luego altas y la nueva elección
        for s in c.simulaciones:
            f = existentes.get(s.id)
            if f is None:
                fila.simulaciones.append(SimulacionORM(
                    id=s.id, origen=s.origen, estilo_id=s.estilo_id, instruccion=s.instruccion,
                    tipo_corte=s.tipo_corte, fuente_prompt=FuentePrompt(s.fuente_prompt),
                    modo=ModoSimulacion(s.modo), latencia_ms=s.latencia_ms, creada_en=s.creada_en,
                    elegida_en=s.elegida_en))
            else:
                f.elegida_en = s.elegida_en
        self.db.flush()
