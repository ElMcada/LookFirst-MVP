import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.iam.domain.usuario import Rol
from app.shared.db import Base, enum_columna


class UsuarioORM(Base):
    """Personal del salón que usa la plataforma. Los clientes NO tienen cuenta (no se guardan sus datos)."""
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "iam", "comment": "Personal del salón (administrador y estilistas)"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, comment="Siempre en minúsculas")
    password_hash: Mapped[str] = mapped_column(String(255), comment="scrypt; nunca la contraseña en claro")
    rol: Mapped[Rol] = mapped_column(enum_columna(Rol, "rol_usuario", "iam"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
