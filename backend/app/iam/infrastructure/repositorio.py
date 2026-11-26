import uuid

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.iam.domain.usuario import Rol, Usuario
from app.iam.infrastructure.orm import UsuarioORM
from app.shared.kernel import a_utc


def _a_dominio(f: UsuarioORM) -> Usuario:
    return Usuario(id=f.id, nombre=f.nombre, email=f.email, password_hash=f.password_hash,
                   rol=f.rol, activo=f.activo, creado_en=a_utc(f.creado_en))


class RepositorioUsuariosSQL:
    def __init__(self, db: Session):
        self.db = db

    def por_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        fila = self.db.get(UsuarioORM, usuario_id)
        return _a_dominio(fila) if fila else None

    def por_email(self, email: str) -> Usuario | None:
        fila = self.db.scalar(select(UsuarioORM).where(UsuarioORM.email == email))
        return _a_dominio(fila) if fila else None

    def listar(self) -> list[Usuario]:
        return [_a_dominio(f) for f in self.db.scalars(select(UsuarioORM).order_by(UsuarioORM.nombre))]

    def guardar(self, u: Usuario) -> None:
        fila = self.db.get(UsuarioORM, u.id) or UsuarioORM(id=u.id, creado_en=u.creado_en)
        fila.nombre, fila.email, fila.password_hash, fila.rol, fila.activo = u.nombre, u.email, u.password_hash, u.rol, u.activo
        self.db.add(fila)
        self.db.flush()

    def hay_admin(self) -> bool:
        return bool(self.db.scalar(select(exists().where(UsuarioORM.rol == Rol.ADMIN))))
