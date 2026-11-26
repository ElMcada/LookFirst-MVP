import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.shared.errores import EntradaInvalida
from app.shared.kernel import ahora

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


class Rol(str, Enum):
    ADMIN = "admin"          # dueño/gerente del salón: gestiona catálogo y estilistas
    ESTILISTA = "estilista"  # opera las consultas con el cliente


def normalizar_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise EntradaInvalida("Correo electrónico no válido.")
    return email


def validar_password(password: str) -> None:
    if len(password or "") < MIN_PASSWORD:
        raise EntradaInvalida(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.")


@dataclass
class Usuario:
    nombre: str
    email: str
    password_hash: str
    rol: Rol
    activo: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creado_en: datetime = field(default_factory=ahora)

    def __post_init__(self):
        self.nombre = (self.nombre or "").strip()
        if not 2 <= len(self.nombre) <= 120:
            raise EntradaInvalida("El nombre debe tener entre 2 y 120 caracteres.")
        self.email = normalizar_email(self.email)

    @property
    def es_admin(self) -> bool:
        return self.rol == Rol.ADMIN
