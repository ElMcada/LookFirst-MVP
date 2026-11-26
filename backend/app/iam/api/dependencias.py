"""Dependencias de autenticación/autorización que usan los demás bounded contexts."""
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.iam.application.servicio_iam import ServicioIAM
from app.iam.domain.usuario import Usuario
from app.iam.infrastructure.repositorio import RepositorioUsuariosSQL
from app.iam.infrastructure.seguridad import EmisorJWT, HasherScrypt
from app.shared.api import get_db
from app.shared.errores import NoAutenticado, Prohibido

_bearer = HTTPBearer(auto_error=False)


def servicio_iam(request: Request, db: Session = Depends(get_db)) -> ServicioIAM:
    s = request.app.state.settings
    return ServicioIAM(RepositorioUsuariosSQL(db), HasherScrypt(), EmisorJWT(s.jwt_secret, s.jwt_horas))


def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
                   iam: ServicioIAM = Depends(servicio_iam)) -> Usuario:
    if not cred:
        raise NoAutenticado("Inicia sesión para continuar.")
    return iam.usuario_desde_token(cred.credentials)


def solo_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if not usuario.es_admin:
        raise Prohibido("Solo el administrador del salón puede realizar esta acción.")
    return usuario
