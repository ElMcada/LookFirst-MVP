"""Reglas para armar el prompt y el negative prompt según el tipo de cambio.

Antes el servidor de Colab aplicaba 'hair on scalp' como negativo a TODOS los pedidos (solo sirve para calvo)
y añadía 'realistic hair texture' incluso al pedir calvo. Ahora el backend decide ambos por tipo de corte.
"""
from app.shared.kernel import TipoCorte
from app.simulacion.domain.modelos import EspecificacionLook

NEG_BASE = "deformed face, distorted eyes, extra eyes, changed facial features, blurry, cartoon, painting, hat, text, watermark"
NEGATIVOS = {
    TipoCorte.CALVO: "hair, hair on scalp, wig, stubble",
    TipoCorte.CONSERVAR: "different haircut, change of hair length, bald, wig",
}


def prompt_final(espec: EspecificacionLook) -> str:
    if espec.tipo_corte == TipoCorte.CALVO:
        return f"{espec.prompt_en}, natural scalp skin matching the face, salon photography, high quality"
    return f"{espec.prompt_en}, realistic hair texture, natural salon lighting, salon photography, high quality"


def negative_prompt(tipo_corte: TipoCorte) -> str:
    return f"{NEG_BASE}, {NEGATIVOS.get(tipo_corte, 'bald, wig')}"
