"""Motor de recomendación por visagismo (REQ-07)."""
from app.catalogo.domain.estilo import Estilo, TipoServicio
from app.shared.kernel import FormaRostro

RAZONES = {
    FormaRostro.OVALADO: "Tu rostro ovalado es equilibrado: admite casi cualquier largo.",
    FormaRostro.REDONDO: "Para un rostro redondo conviene alargar con capas y largo bajo la mandíbula.",
    FormaRostro.CUADRADO: "Para un rostro cuadrado conviene suavizar la mandíbula con capas y ondas.",
    FormaRostro.ALARGADO: "Para un rostro alargado conviene dar volumen lateral y largos medios.",
}


def recomendar(estilos: list[Estilo], forma: FormaRostro, cantidad: int = 4) -> list[Estilo]:
    """Solo estilos compatibles; intercala cortes y tintes para no mostrar solo un tipo de servicio."""
    compatibles = [e for e in estilos if e.recomendable_para(forma)]
    cortes = [e for e in compatibles if e.tipo == TipoServicio.CORTE]
    tintes = [e for e in compatibles if e.tipo == TipoServicio.TINTE]
    mezcla: list[Estilo] = []
    while (cortes or tintes) and len(mezcla) < cantidad:
        if cortes:
            mezcla.append(cortes.pop(0))
        if tintes and len(mezcla) < cantidad:
            mezcla.append(tintes.pop(0))
    return mezcla
