import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.iam.api.dependencias import servicio_iam, solo_admin, usuario_actual
from app.iam.application.servicio_iam import ServicioIAM
from app.iam.domain.usuario import Rol, Usuario

router = APIRouter(tags=["IAM"])


class LoginIn(BaseModel):
    email: str
    password: str


class UsuarioIn(BaseModel):
    nombre: str
    email: str
    password: str
    rol: Rol = Rol.ESTILISTA


class EstadoIn(BaseModel):
    activo: bool


def usuario_out(u: Usuario) -> dict:
    return {"id": str(u.id), "nombre": u.nombre, "email": u.email, "rol": u.rol.value, "activo": u.activo}


@router.post("/auth/login")
def login(body: LoginIn, iam: ServicioIAM = Depends(servicio_iam)):
    token, u = iam.iniciar_sesion(body.email, body.password)
    return {"token": token, "usuario": usuario_out(u)}


@router.get("/auth/me")
def yo(u: Usuario = Depends(usuario_actual)):
    return usuario_out(u)


@router.get("/usuarios")
def listar(_: Usuario = Depends(solo_admin), iam: ServicioIAM = Depends(servicio_iam)):
    return [usuario_out(u) for u in iam.listar()]


@router.post("/usuarios", status_code=201)
def registrar(body: UsuarioIn, _: Usuario = Depends(solo_admin), iam: ServicioIAM = Depends(servicio_iam)):
    return usuario_out(iam.registrar(body.nombre, body.email, body.password, body.rol))


@router.patch("/usuarios/{usuario_id}")
def cambiar_estado(usuario_id: uuid.UUID, body: EstadoIn, actor: Usuario = Depends(solo_admin),
                   iam: ServicioIAM = Depends(servicio_iam)):
    return usuario_out(iam.cambiar_estado(actor, usuario_id, body.activo))
