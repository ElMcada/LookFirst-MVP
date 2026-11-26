"""Intérprete con LLM (Groq o Gemini): traduce el español coloquial a una especificación técnica."""
import json
import re

from app.shared.kernel import TipoCorte
from app.simulacion.domain.modelos import EspecificacionLook, FuentePrompt

SYSTEM = (
    "You are a senior hair stylist assistant in a Peruvian salon. Convert the client's colloquial Spanish request "
    "into a technical spec for a Stable Diffusion inpainting model that edits ONLY the hair. "
    'Respond with ONLY valid JSON: {"prompt_en": string|null, "color_hex": "#RRGGBB"|null, '
    '"tipo_corte": "conservar"|"calvo"|"corto"|"medio"|"largo", "degradado": boolean}. '
    "Rules: "
    "prompt_en (<= 35 words, English) describes ONLY the target hairstyle, length, texture and/or color; no quality buzzwords. "
    "If bald/shaved ('calvo', 'rapado', 'pelado'), use 'completely bald head, cleanly shaved smooth scalp, bare neck and shoulders' and never the word hair. "
    "If short cut ('corto', 'pixie', 'buzz', 'fade'), explicitly include 'short cropped hair above ears, bare neck and shoulders visible' so long hair is removed. "
    "If long hair ('largo', 'melena larga'), explicitly include 'long hair flowing past the shoulders'. "
    "If wavy/curly ('ondulado', 'rizado', 'ondas'), include 'defined wavy textured hair'. "
    "For ANY color request, always include 'rich saturated salon hair dye, uniform full hair color from roots to tips'. "
    "tipo_corte: 'conservar' when changing ONLY color OR ONLY texture (wavy/straight) without changing length; "
    "'calvo' shaved head; 'corto' pixie/buzz/fade/short; 'medio' bob/lob/bangs/shoulder length; 'largo' long hair past shoulders. "
    "color_hex: dominant target color, or null if no color change or bald. "
    "degradado: true for balayage, ombré, highlights or root-to-tip gradients. "
    "If the request is not about hair, return prompt_en null."
)


def _parsear(txt: str, texto_original: str) -> EspecificacionLook | None:
    m = re.search(r"\{.*\}", txt or "", re.S)
    if not m:
        return None
    data = json.loads(m.group(0))
    prompt = data.get("prompt_en")
    if not isinstance(prompt, str) or len(prompt.strip()) < 5:
        return None
    try:
        tipo = TipoCorte(data.get("tipo_corte"))
    except ValueError:
        return None
    hx = data.get("color_hex")
    hx = hx.upper() if isinstance(hx, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", hx) else None
    if tipo == TipoCorte.CALVO:
        hx = None
    if tipo == TipoCorte.CONSERVAR and not hx:
        return None  # "solo color" sin color: respuesta incoherente, mejor el respaldo
    return EspecificacionLook(prompt_en=prompt.strip()[:300], tipo_corte=tipo, fuente=FuentePrompt.LLM,
                              color_hex=hx, degradado=bool(data.get("degradado")))


class InterpreteGroq:
    def __init__(self, api_key: str, modelo: str):
        from groq import Groq
        self._cliente, self.modelo = Groq(api_key=api_key), modelo

    def interpretar(self, texto: str) -> EspecificacionLook | None:
        r = self._cliente.chat.completions.create(
            model=self.modelo, temperature=0.2, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": texto}])
        return _parsear(r.choices[0].message.content, texto)


class InterpreteGemini:
    def __init__(self, api_key: str, modelo: str):
        from google import genai
        self._cliente, self.modelo = genai.Client(api_key=api_key), modelo

    def interpretar(self, texto: str) -> EspecificacionLook | None:
        r = self._cliente.models.generate_content(model=self.modelo, contents=f"{SYSTEM}\nClient request: {texto}")
        return _parsear(r.text, texto)
