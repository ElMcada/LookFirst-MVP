import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.catalogo.application.servicio_catalogo import ServicioCatalogo
from app.catalogo.domain.estilo import Estilo, TipoServicio
from app.catalogo.infrastructure.repositorio import RepositorioEstilosSQL
from app.iam.api.dependencias import solo_admin, usuario_actual
from app.iam.domain.usuario import Usuario
from app.shared.api import get_db
from app.shared.kernel import FormaRostro, TipoCorte

router = APIRouter(prefix="/estilos", tags=["Catálogo"])


def servicio_catalogo(db: Session = Depends(get_db)) -> ServicioCatalogo:
    return ServicioCatalogo(RepositorioEstilosSQL(db))


class EstiloIn(BaseModel):
    codigo: str
    nombre: str
    tipo: TipoServicio
    descripcion: str = ""
    prompt_en: str
    tipo_corte: TipoCorte
    formas: list[FormaRostro] = Field(min_length=1)
    color_hex: str | None = None
    degradado: bool = False


class EstadoIn(BaseModel):
    activo: bool


def estilo_out(e: Estilo) -> dict:
    return {"id": str(e.id), "codigo": e.codigo, "nombre": e.nombre, "tipo": e.tipo.value,
            "descripcion": e.descripcion, "prompt_en": e.prompt_en, "tipo_corte": e.tipo_corte.value,
            "formas": sorted(f.value for f in e.formas), "color_hex": e.color_hex,
            "degradado": e.degradado, "activo": e.activo}


@router.get("")
def listar(todos: bool = False, u: Usuario = Depends(usuario_actual), cat: ServicioCatalogo = Depends(servicio_catalogo)):
    return [estilo_out(e) for e in cat.listar(incluir_inactivos=todos and u.es_admin)]


@router.post("", status_code=201)
def crear(body: EstiloIn, _: Usuario = Depends(solo_admin), cat: ServicioCatalogo = Depends(servicio_catalogo)):
    return estilo_out(cat.crear(body.model_dump()))


@router.put("/{estilo_id}")
def actualizar(estilo_id: uuid.UUID, body: EstiloIn, _: Usuario = Depends(solo_admin),
               cat: ServicioCatalogo = Depends(servicio_catalogo)):
    return estilo_out(cat.actualizar(estilo_id, body.model_dump()))


@router.patch("/{estilo_id}")
def cambiar_estado(estilo_id: uuid.UUID, body: EstadoIn, _: Usuario = Depends(solo_admin),
                   cat: ServicioCatalogo = Depends(servicio_catalogo)):
    return estilo_out(cat.cambiar_estado(estilo_id, body.activo))
