import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalogo.domain.estilo import TipoServicio
from app.shared.db import Base, enum_columna
from app.shared.kernel import FormaRostro, TipoCorte


class EstiloORM(Base):
    __tablename__ = "estilos"
    __table_args__ = (
        CheckConstraint("color_hex IS NULL OR color_hex ~ '^#[0-9A-F]{6}$'", name="ck_estilos_color_hex")
        .ddl_if(dialect="postgresql"),
        # Un tinte conserva la silueta y siempre tiene color; un corte siempre cambia el largo.
        CheckConstraint("(tipo = 'tinte') = (tipo_corte = 'conservar')", name="ck_estilos_tinte_conserva"),
        CheckConstraint("tipo <> 'tinte' OR color_hex IS NOT NULL", name="ck_estilos_tinte_color"),
        {"schema": "catalogo", "comment": "Servicios de corte y tinte que el salón ofrece (REQ-10)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    nombre: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[TipoServicio] = mapped_column(enum_columna(TipoServicio, "tipo_servicio", "catalogo"))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    prompt_en: Mapped[str] = mapped_column(String(400), comment="Descripción técnica para el modelo de inpainting")
    tipo_corte: Mapped[TipoCorte] = mapped_column(enum_columna(TipoCorte, "tipo_corte", "catalogo"))
    color_hex: Mapped[str | None] = mapped_column(String(7))
    degradado: Mapped[bool] = mapped_column(Boolean, default=False, comment="Balayage/ombré: color más intenso en puntas")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, comment="Se desactiva en vez de borrar")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    formas: Mapped[list["EstiloFormaORM"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class EstiloFormaORM(Base):
    """Formas de rostro para las que se recomienda un estilo (relación N:M con un conjunto fijo)."""
    __tablename__ = "estilo_formas_rostro"
    __table_args__ = {"schema": "catalogo"}

    estilo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("catalogo.estilos.id", ondelete="CASCADE"), primary_key=True)
    forma: Mapped[FormaRostro] = mapped_column(enum_columna(FormaRostro, "forma_rostro", "catalogo"), primary_key=True)
