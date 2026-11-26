import uuid

from app.iam.domain.puertos import EmisorTokens, HasherContrasenas, RepositorioUsuarios
from app.iam.domain.usuario import Rol, Usuario, normalizar_email, validar_password
from app.shared.errores import Conflicto, EntradaInvalida, NoAutenticado, NoEncontrado

CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos."


class ServicioIAM:
    def __init__(self, repo: RepositorioUsuarios, hasher: HasherContrasenas, tokens: EmisorTokens):
        self.repo, self.hasher, self.tokens = repo, hasher, tokens

    def iniciar_sesion(self, email: str, password: str) -> tuple[str, Usuario]:
        try:
            usuario = self.repo.por_email(normalizar_email(email))
        except EntradaInvalida:
            usuario = None
        if not usuario or not self.hasher.verificar(password or "", usuario.password_hash):
            raise NoAutenticado(CREDENCIALES_INVALIDAS)
        if not usuario.activo:
            raise NoAutenticado("Tu cuenta está desactivada. Contacta al administrador del salón.")
        return self.tokens.emitir(usuario), usuario

    def usuario_desde_token(self, token: str) -> Usuario:
        usuario = self.repo.por_id(self.tokens.leer(token))
        if not usuario or not usuario.activo:
            raise NoAutenticado("Sesión no válida. Inicia sesión de nuevo.")
        return usuario

    def registrar(self, nombre: str, email: str, password: str, rol: Rol) -> Usuario:
        validar_password(password)
        usuario = Usuario(nombre=nombre, email=email, password_hash=self.hasher.hashear(password), rol=rol)
        if self.repo.por_email(usuario.email):
            raise Conflicto("Ya existe un usuario con ese correo.")
        self.repo.guardar(usuario)
        return usuario

    def listar(self) -> list[Usuario]:
        return self.repo.listar()

    def cambiar_estado(self, actor: Usuario, usuario_id: uuid.UUID, activo: bool) -> Usuario:
        usuario = self.repo.por_id(usuario_id)
        if not usuario:
            raise NoEncontrado("Usuario no encontrado.")
        if usuario.id == actor.id and not activo:
            raise Conflicto("No puedes desactivar tu propia cuenta.")
        usuario.activo = activo
        self.repo.guardar(usuario)
        return usuario

    def asegurar_admin_inicial(self, nombre: str, email: str, password: str) -> Usuario | None:
        """Crea el primer administrador desde .env si la BD aún no tiene ninguno."""
        if self.repo.hay_admin() or not email or not password:
            return None
        return self.registrar(nombre, email, password, Rol.ADMIN)
