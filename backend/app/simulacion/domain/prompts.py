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
    refuerzos = {
        TipoCorte.LARGO: "(long voluminous hair falling past shoulders:1.35), (cascading strands framing face and neck:1.25), ",
        TipoCorte.MEDIO: "(shoulder-length medium haircut:1.3), (clean bare neck below shoulders:1.2), ",
        TipoCorte.CORTO: "(short cropped haircut above the ears:1.35), (completely bare neck and shoulders:1.3), ",
        TipoCorte.CALVO: "(completely bald head, smooth shaved scalp:1.4), (bare neck and shoulders:1.3), ",
    }
    prefijo = refuerzos.get(espec.tipo_corte, "")
    return f"{prefijo}{espec.prompt_en}, photorealistic salon portrait photography, natural hair texture, realistic lighting"


def negative_prompt(tipo_corte: TipoCorte) -> str:
    return f"{NEG_BASE}, {NEGATIVOS.get(tipo_corte, 'bald, wig')}"
