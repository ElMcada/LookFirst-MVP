import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.consulta.domain.consulta import EstadoConsulta, OrigenSolicitud
from app.shared.db import Base, enum_columna
from app.shared.kernel import TipoCorte
from app.simulacion.domain.modelos import FuentePrompt, ModoSimulacion


class ConsultaORM(Base):
    """Una atención en el sillón. Anónima: no hay nombre, DNI, foto ni rasgos faciales del cliente."""
    __tablename__ = "consultas"
    __table_args__ = (
        CheckConstraint("satisfaccion BETWEEN 1 AND 10", name="ck_consultas_satisfaccion"),
        CheckConstraint("(estado = 'activa') = (finalizada_en IS NULL)", name="ck_consultas_cierre"),
        # Ley 29733: toda consulta cerrada debe tener constancia del borrado de la foto
        CheckConstraint("finalizada_en IS NULL OR datos_eliminados_en IS NOT NULL", name="ck_consultas_borrado"),
        CheckConstraint("satisfaccion IS NULL OR estado = 'finalizada'", name="ck_consultas_satisfaccion_estado"),
        Index("ix_consultas_estilista_fecha", "estilista_id", "iniciada_en"),
        Index("ix_consultas_activas", "iniciada_en", postgresql_where=text("estado = 'activa'")),
        {"schema": "consulta", "comment": "Consultas de asesoría (anónimas, sin datos biométricos)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    estilista_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("iam.usuarios.id", ondelete="RESTRICT"))
    estado: Mapped[EstadoConsulta] = mapped_column(enum_columna(EstadoConsulta, "estado_consulta", "consulta"))
    consentimiento_version: Mapped[str] = mapped_column(String(20), comment="Versión del texto legal aceptado")
    consentimiento_otorgado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    iniciada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finalizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    datos_eliminados_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 comment="Constancia de borrado de la foto (REQ-09)")
    satisfaccion: Mapped[int | None] = mapped_column(SmallInteger, comment="1-10, KPI OE4 (> 8)")

    simulaciones: Mapped[list["SimulacionORM"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="SimulacionORM.creada_en")


class SimulacionORM(Base):
    """Cada look probado. Sirve para medir latencia (REQ-04) y tiempo de decisión (OE4)."""
    __tablename__ = "simulaciones"
    __table_args__ = (
        CheckConstraint("latencia_ms >= 0", name="ck_simulaciones_latencia"),
        CheckConstraint("(origen = 'catalogo') = (estilo_id IS NOT NULL)", name="ck_simulaciones_estilo"),
        CheckConstraint("origen = 'catalogo' OR instruccion IS NOT NULL", name="ck_simulaciones_instruccion"),
        # Solo un look elegido por consulta
        Index("uq_simulaciones_elegida", "consulta_id", unique=True,
              postgresql_where=text("elegida_en IS NOT NULL"), sqlite_where=text("elegida_en IS NOT NULL")),
        Index("ix_simulaciones_creada", "creada_en"),
        {"schema": "consulta"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    consulta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("consulta.consultas.id", ondelete="CASCADE"), index=True)
    origen: Mapped[OrigenSolicitud] = mapped_column(enum_columna(OrigenSolicitud, "origen_solicitud", "consulta"))
    estilo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("catalogo.estilos.id", ondelete="RESTRICT"))
    instruccion: Mapped[str | None] = mapped_column(String(300), comment="Texto o voz transcrita del pedido")
    tipo_corte: Mapped[TipoCorte] = mapped_column(enum_columna(TipoCorte, "tipo_corte", "consulta"))
    fuente_prompt: Mapped[FuentePrompt] = mapped_column(enum_columna(FuentePrompt, "fuente_prompt", "consulta"))
    modo: Mapped[ModoSimulacion] = mapped_column(enum_columna(ModoSimulacion, "modo_simulacion", "consulta"))
    latencia_ms: Mapped[int] = mapped_column(Integer)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    elegida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="Momento en que el cliente decidió")
