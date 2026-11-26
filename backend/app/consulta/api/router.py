import base64
import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.catalogo.application.servicio_catalogo import ServicioCatalogo
from app.catalogo.infrastructure.repositorio import RepositorioEstilosSQL
from app.consulta.application.servicio_consulta import ServicioConsulta
from app.consulta.domain.consulta import VERSION_CONSENTIMIENTO, Consulta, OrigenSolicitud
from app.consulta.infrastructure.proveedor_estilos import ProveedorEstilosCatalogo
from app.consulta.infrastructure.repositorio import RepositorioConsultasSQL
from app.iam.api.dependencias import usuario_actual
from app.iam.domain.usuario import Usuario
from app.shared.api import get_db

router = APIRouter(prefix="/consultas", tags=["Consulta"])


def construir_servicio(state, db: Session) -> ServicioConsulta:
    return ServicioConsulta(RepositorioConsultasSQL(db), state.fotos,
                            ProveedorEstilosCatalogo(ServicioCatalogo(RepositorioEstilosSQL(db))),
                            state.motor, state.settings.latency_budget)


def servicio_consulta(request: Request, db: Session = Depends(get_db)) -> ServicioConsulta:
    return construir_servicio(request.app.state, db)


class IniciarIn(BaseModel):
    acepta_consentimiento: bool
    version_consentimiento: str


class SimularIn(BaseModel):
    origen: OrigenSolicitud
    estilo_id: uuid.UUID | None = None
    instruccion: str | None = Field(default=None, max_length=300)


class FinalizarIn(BaseModel):
    satisfaccion: int | None = Field(default=None, ge=1, le=10)


def consulta_out(c: Consulta) -> dict:
    return {"id": str(c.id), "estado": c.estado.value, "iniciada_en": c.iniciada_en.isoformat(),
            "finalizada_en": c.finalizada_en and c.finalizada_en.isoformat(),
            "datos_eliminados_en": c.datos_eliminados_en and c.datos_eliminados_en.isoformat()}


@router.get("/consentimiento")
def version_consentimiento():
    return {"version": VERSION_CONSENTIMIENTO}


@router.post("", status_code=201)
def iniciar(body: IniciarIn, u: Usuario = Depends(usuario_actual), svc: ServicioConsulta = Depends(servicio_consulta)):
    return consulta_out(svc.iniciar(u.id, body.acepta_consentimiento, body.version_consentimiento))


@router.post("/{consulta_id}/foto")
def analizar_foto(consulta_id: uuid.UUID, file: UploadFile = File(...), u: Usuario = Depends(usuario_actual),
                  svc: ServicioConsulta = Depends(servicio_consulta)):
    return svc.analizar_foto(u.id, consulta_id, file.file.read())


@router.post("/{consulta_id}/simulaciones", status_code=201)
def simular(consulta_id: uuid.UUID, body: SimularIn, u: Usuario = Depends(usuario_actual),
            svc: ServicioConsulta = Depends(servicio_consulta)):
    r = svc.simular(u.id, consulta_id, body.origen, body.estilo_id, body.instruccion)
    s = r.simulacion
    return {"id": str(s.id), "etiqueta": r.etiqueta, "imagen_b64": base64.b64encode(r.look.imagen_jpg).decode(),
            "latencia_s": round(s.latencia_ms / 1000, 2), "modo": r.look.modo.value, "tipo_corte": s.tipo_corte.value,
            "fuente_prompt": s.fuente_prompt, "prompt_en": r.prompt_en, "aviso": r.look.aviso}


@router.post("/{consulta_id}/simulaciones/{simulacion_id}/elegir")
def elegir(consulta_id: uuid.UUID, simulacion_id: uuid.UUID, u: Usuario = Depends(usuario_actual),
           svc: ServicioConsulta = Depends(servicio_consulta)):
    s = svc.elegir_look(u.id, consulta_id, simulacion_id)
    return {"id": str(s.id), "elegida_en": s.elegida_en.isoformat()}


@router.post("/{consulta_id}/finalizar")
def finalizar(consulta_id: uuid.UUID, body: FinalizarIn, u: Usuario = Depends(usuario_actual),
              svc: ServicioConsulta = Depends(servicio_consulta)):
    return consulta_out(svc.finalizar(u.id, consulta_id, body.satisfaccion))


@router.post("/{consulta_id}/revocar")
def revocar(consulta_id: uuid.UUID, u: Usuario = Depends(usuario_actual),
            svc: ServicioConsulta = Depends(servicio_consulta)):
    return consulta_out(svc.revocar_consentimiento(u.id, consulta_id))
