import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalogo.domain.estilo import Estilo
from app.catalogo.infrastructure.orm import EstiloFormaORM, EstiloORM


def _a_dominio(f: EstiloORM) -> Estilo:
    return Estilo(id=f.id, codigo=f.codigo, nombre=f.nombre, tipo=f.tipo, descripcion=f.descripcion,
                  prompt_en=f.prompt_en, tipo_corte=f.tipo_corte, formas={x.forma for x in f.formas},
                  color_hex=f.color_hex, degradado=f.degradado, activo=f.activo)


class RepositorioEstilosSQL:
    def __init__(self, db: Session):
        self.db = db

    def por_id(self, estilo_id: uuid.UUID) -> Estilo | None:
        fila = self.db.get(EstiloORM, estilo_id)
        return _a_dominio(fila) if fila else None

    def por_codigo(self, codigo: str) -> Estilo | None:
        fila = self.db.scalar(select(EstiloORM).where(EstiloORM.codigo == codigo))
        return _a_dominio(fila) if fila else None

    def listar(self, solo_activos: bool) -> list[Estilo]:
        q = select(EstiloORM).order_by(EstiloORM.tipo, EstiloORM.nombre)
        if solo_activos:
            q = q.where(EstiloORM.activo.is_(True))
        return [_a_dominio(f) for f in self.db.scalars(q)]

    def guardar(self, e: Estilo) -> None:
        fila = self.db.get(EstiloORM, e.id) or EstiloORM(id=e.id)
        fila.codigo, fila.nombre, fila.tipo, fila.descripcion = e.codigo, e.nombre, e.tipo, e.descripcion
        fila.prompt_en, fila.tipo_corte, fila.color_hex = e.prompt_en, e.tipo_corte, e.color_hex
        fila.degradado, fila.activo = e.degradado, e.activo
        actuales = {x.forma: x for x in fila.formas}
        fila.formas = [actuales.get(f) or EstiloFormaORM(forma=f) for f in sorted(e.formas, key=lambda f: f.value)]
        self.db.add(fila)
        self.db.flush()

    def contar(self) -> int:
        return self.db.scalar(select(func.count()).select_from(EstiloORM)) or 0
