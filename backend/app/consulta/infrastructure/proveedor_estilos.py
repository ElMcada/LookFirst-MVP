"""Capa anticorrupción: traduce el modelo del Catálogo al lenguaje de la Consulta."""
import uuid

from app.catalogo.api.router import estilo_out
from app.catalogo.application.servicio_catalogo import ServicioCatalogo
from app.consulta.domain.puertos import EstiloOfrecido
from app.shared.kernel import FormaRostro


class ProveedorEstilosCatalogo:
    def __init__(self, catalogo: ServicioCatalogo):
        self.catalogo = catalogo

    def obtener(self, estilo_id: uuid.UUID) -> EstiloOfrecido:
        e = self.catalogo.obtener_activo(estilo_id)
        return EstiloOfrecido(id=e.id, nombre=e.nombre, prompt_en=e.prompt_en, tipo_corte=e.tipo_corte,
                              color_hex=e.color_hex, degradado=e.degradado)

    def recomendar(self, forma: FormaRostro) -> tuple[str, list[dict]]:
        razon, estilos = self.catalogo.recomendar(forma)
        return razon, [estilo_out(e) for e in estilos]
