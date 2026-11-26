"""Intérprete de respaldo por palabras clave (sin internet). Se usa si el LLM falla o tarda."""
from app.shared.kernel import TipoCorte
from app.simulacion.domain.modelos import EspecificacionLook, FuentePrompt

# Del más específico al más general: gana la primera coincidencia.
COLORES = [
    ("rubio platin", "platinum blonde", "#E6DFD3"), ("platinado", "platinum blonde", "#E6DFD3"),
    ("rubio ceniza", "ash blonde", "#BDB2A0"), ("ceniza", "ash blonde", "#BDB2A0"),
    ("rubio miel", "honey blonde", "#C99E59"), ("miel", "honey blonde", "#C99E59"),
    ("rubio dorado", "golden blonde", "#D4B06A"), ("rubio oscuro", "dark dirty blonde", "#8C7355"),
    ("rubio", "golden blonde", "#D4B06A"),
    ("cobrizo", "warm copper", "#B4592B"), ("cobre", "warm copper", "#B4592B"),
    ("caoba", "mahogany auburn", "#6E2622"), ("pelirroj", "vibrant ginger red", "#A8321E"),
    ("borgo", "deep burgundy", "#6B1D2F"), ("burdeos", "deep burgundy", "#6B1D2F"),
    ("vino", "wine red", "#6B1D2F"), ("rojo", "vibrant red", "#B3202A"),
    ("castaño claro", "light caramel brown", "#7C5638"), ("castaño oscuro", "dark espresso brown", "#2E1D16"),
    ("chocolate", "rich chocolate brown", "#4B2E22"), ("caramelo", "caramel brown", "#8E5B37"),
    ("casta", "chestnut brown", "#5A3A28"), ("marrón", "chestnut brown", "#5A3A28"),
    ("negro azulado", "blue-black", "#11141D"), ("negro", "jet black", "#16110F"),
    ("rosa pastel", "pastel pink", "#E59AB0"), ("fucsia", "vibrant magenta pink", "#C2276B"),
    ("rosa", "pastel pink", "#E59AB0"), ("morado", "deep violet purple", "#5A2D82"),
    ("violeta", "lavender violet", "#8868A8"), ("lila", "pastel lilac", "#B49AC9"),
    ("azul", "midnight blue", "#2C5AA0"), ("turquesa", "teal turquoise", "#25898E"),
    ("verde", "emerald green", "#236B48"), ("plate", "silver gray", "#B9BCC2"),
    ("canas", "natural salt and pepper gray", "#9EA2A8"), ("gris", "silver gray", "#B9BCC2"),
]
CORTES = [
    (("calvo", "rapado", "pelado", "sin pelo"), TipoCorte.CALVO, "completely bald head, cleanly shaved smooth scalp, bare neck and shoulders"),
    (("buzz", "al cero", "militar"), TipoCorte.CORTO, "ultra short buzz cut, clean fade on the sides, bare neck"),
    (("pixie", "duendecillo", "muy corto"), TipoCorte.CORTO, "chic textured short pixie haircut above the ears, bare neck and shoulders"),
    (("corto", "degradado", "fade"), TipoCorte.CORTO, "modern short tapered haircut above the ears, clean faded sides, bare neck"),
    (("long bob", "media melena", "lob"), TipoCorte.MEDIO, "shoulder-length long bob haircut, clean neck below shoulders"),
    (("bob", "carré", "melena corta"), TipoCorte.MEDIO, "classic chin-length bob haircut, bare neck and shoulders"),
    (("flequillo", "cerquillo", "bangs"), TipoCorte.MEDIO, "hairstyle with soft curtain bangs framing the forehead"),
    (("capas", "degrafilado", "layered"), TipoCorte.LARGO, "long layered haircut flowing past the shoulders"),
    (("largo", "melena larga", "long hair"), TipoCorte.LARGO, "long hair extending past the shoulders"),
]
TEXTURAS = [
    (("ondas", "ondulado", "waves"), "defined wavy hair with soft waves"),
    (("rizos", "rizado", "crespo", "curly"), "defined curly hair with voluminous curls"),
    (("lacio", "liso", "planchado", "straight"), "sleek straight silky hair"),
]
PALABRAS_DEGRADADO_COLOR = ("balayage", "ombre", "ombré", "mechas", "californianas", "reflejos", "degradado de color")


class InterpretePalabrasClave:
    def interpretar(self, texto: str) -> EspecificacionLook | None:
        t = (texto or "").lower()
        color = next(((en, hx) for k, en, hx in COLORES if k in t), None)
        degradado = color is not None and any(k in t for k in PALABRAS_DEGRADADO_COLOR + ("degrad",))
        corte = None
        for claves, tipo, desc in CORTES:
            # 'degradado' con un color es un tinte (ombré), no un corte fade
            claves_validas = [k for k in claves if not (k == "degradado" and color)]
            if any(k in t for k in claves_validas):
                corte = (tipo, desc)
                break

        textura = next((desc for claves, desc in TEXTURAS if any(k in t for k in claves)), None)

        if corte and corte[0] == TipoCorte.CALVO:
            return EspecificacionLook(prompt_en=corte[1], tipo_corte=TipoCorte.CALVO, fuente=FuentePrompt.PALABRAS_CLAVE)
        if corte or textura:
            tipo = corte[0] if corte else TipoCorte.CONSERVAR
            base_desc = ", ".join(filter(None, [corte[1] if corte else "same hair length", textura]))
            color_desc = f"rich saturated dyed {color[0]} hair color, uniform color from roots to tips" if color else "natural hair color"
            return EspecificacionLook(prompt_en=f"{base_desc}, {color_desc}", tipo_corte=tipo,
                                      fuente=FuentePrompt.PALABRAS_CLAVE, color_hex=color and color[1], degradado=degradado)
        if color:
            estilo = "balayage gradient from natural roots to colored ends" if degradado else "uniform full hair color from roots to tips"
            return EspecificacionLook(
                prompt_en=f"{color[0]} hair color, rich saturated salon hair dye, {estilo}, same haircut and length",
                tipo_corte=TipoCorte.CONSERVAR, fuente=FuentePrompt.PALABRAS_CLAVE, color_hex=color[1], degradado=degradado)
        return None