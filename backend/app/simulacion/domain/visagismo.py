"""Clasificación de la forma del rostro a partir de proporciones de landmarks (heurística de visagismo)."""
from app.shared.kernel import FormaRostro


def clasificar_forma(alto_ancho: float, mandibula_pomulos: float) -> FormaRostro:
    if alto_ancho >= 1.40:
        return FormaRostro.ALARGADO
    if alto_ancho < 1.25:
        return FormaRostro.CUADRADO if mandibula_pomulos >= 0.82 else FormaRostro.REDONDO
    return FormaRostro.CUADRADO if mandibula_pomulos >= 0.86 else FormaRostro.OVALADO
