import json
import uuid
from pathlib import Path

from app.catalogo.domain.estilo import Estilo, TipoServicio
from app.catalogo.domain.puertos import RepositorioEstilos
from app.catalogo.domain.recomendacion import RAZONES, recomendar
from app.shared.errores import Conflicto, NoEncontrado
from app.shared.kernel import FormaRostro, TipoCorte


class ServicioCatalogo:
    def __init__(self, repo: RepositorioEstilos):
        self.repo = repo

    def listar(self, incluir_inactivos: bool = False) -> list[Estilo]:
        return self.repo.listar(solo_activos=not incluir_inactivos)

    def obtener_activo(self, estilo_id: uuid.UUID) -> Estilo:
        estilo = self.repo.por_id(estilo_id)
        if not estilo or not estilo.activo:
            raise NoEncontrado("El estilo no existe o ya no se ofrece en el salón.")
        return estilo

    def recomendar(self, forma: FormaRostro) -> tuple[str, list[Estilo]]:
        return RAZONES[forma], recomendar(self.repo.listar(solo_activos=True), forma)

    def crear(self, datos: dict) -> Estilo:
        estilo = Estilo(**datos)
        if self.repo.por_codigo(estilo.codigo):
            raise Conflicto("Ya existe un estilo con ese código.")
        self.repo.guardar(estilo)
        return estilo

    def actualizar(self, estilo_id: uuid.UUID, datos: dict) -> Estilo:
        actual = self.repo.por_id(estilo_id)
        if not actual:
            raise NoEncontrado("Estilo no encontrado.")
        nuevo = Estilo(id=actual.id, activo=actual.activo, **datos)
        otro = self.repo.por_codigo(nuevo.codigo)
        if otro and otro.id != actual.id:
            raise Conflicto("Ya existe un estilo con ese código.")
        self.repo.guardar(nuevo)
        return nuevo

    def cambiar_estado(self, estilo_id: uuid.UUID, activo: bool) -> Estilo:
        """Los estilos no se borran: las simulaciones históricas los referencian."""
        estilo = self.repo.por_id(estilo_id)
        if not estilo:
            raise NoEncontrado("Estilo no encontrado.")
        estilo.activo = activo
        self.repo.guardar(estilo)
        return estilo

    def sembrar_si_vacio(self, archivo: Path) -> int:
        if self.repo.contar() or not archivo.exists():
            return 0
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        for d in datos:
            self.repo.guardar(Estilo(
                codigo=d["codigo"], nombre=d["nombre"], tipo=TipoServicio(d["tipo"]), descripcion=d["descripcion"],
                prompt_en=d["prompt_en"], tipo_corte=TipoCorte(d["tipo_corte"]),
                formas={FormaRostro(f) for f in d["formas"]}, color_hex=d.get("color_hex"),
                degradado=d.get("degradado", False)))
        return len(datos)
