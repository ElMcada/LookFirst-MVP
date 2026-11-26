import base64
import hashlib
import hmac
import os
import uuid
from datetime import timedelta

import jwt

from app.iam.domain.usuario import Usuario
from app.shared.errores import NoAutenticado
from app.shared.kernel import ahora


class HasherScrypt:
    """scrypt de la librería estándar: resistente a fuerza bruta y sin dependencias nativas."""
    N, R, P, LARGO = 2 ** 14, 8, 1, 32

    def hashear(self, password: str) -> str:
        sal = os.urandom(16)
        h = hashlib.scrypt(password.encode(), salt=sal, n=self.N, r=self.R, p=self.P, dklen=self.LARGO)
        b64 = lambda b: base64.b64encode(b).decode()
        return f"scrypt${self.N}${self.R}${self.P}${b64(sal)}${b64(h)}"

    def verificar(self, password: str, password_hash: str) -> bool:
        try:
            _, n, r, p, sal, esperado = password_hash.split("$")
            h = hashlib.scrypt(password.encode(), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p),
                               dklen=len(base64.b64decode(esperado)))
            return hmac.compare_digest(h, base64.b64decode(esperado))
        except (ValueError, TypeError):
            return False


class EmisorJWT:
    ALG = "HS256"

    def __init__(self, secreto: str, horas: int):
        self.secreto, self.horas = secreto, horas

    def emitir(self, usuario: Usuario) -> str:
        t = ahora()
        payload = {"sub": str(usuario.id), "rol": usuario.rol.value, "iat": t, "exp": t + timedelta(hours=self.horas)}
        return jwt.encode(payload, self.secreto, algorithm=self.ALG)

    def leer(self, token: str) -> uuid.UUID:
        try:
            return uuid.UUID(jwt.decode(token, self.secreto, algorithms=[self.ALG])["sub"])
        except jwt.ExpiredSignatureError:
            raise NoAutenticado("Tu sesión expiró. Inicia sesión de nuevo.")
        except (jwt.PyJWTError, KeyError, ValueError):
            raise NoAutenticado("Sesión no válida. Inicia sesión de nuevo.")
