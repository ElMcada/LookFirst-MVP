"""Operaciones puras de imagen (sin E/S): máscaras, recorte, mezcla y tinte local."""
import io

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.shared.errores import EntradaInvalida
from app.shared.kernel import TipoCorte

MAX_BYTES = 12 * 1024 * 1024
LADO_MODELO = 512


def decodificar(raw: bytes, max_lado: int) -> np.ndarray:
    if not raw or len(raw) > MAX_BYTES:
        raise EntradaInvalida("Imagen vacía o demasiado grande (máx. 12 MB).")
    try:
        pil = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except Exception:
        raise EntradaInvalida("El archivo no es una imagen válida.")
    pil.thumbnail((max_lado, max_lado))
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def codificar_jpg(bgr: np.ndarray, calidad: int = 90) -> bytes:
    return cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, calidad])[1].tobytes()

def mascara_trabajo(mascara: np.ndarray, escudo: np.ndarray, tipo_corte: TipoCorte) -> np.ndarray:
    """Zona que el modelo puede redibujar según el cambio pedido; protege el centro facial pero libera el contorno."""
    h, w = mascara.shape[:2]
    # Erosiona el escudo facial para liberar línea del cabello, patillas y bordes de mandíbula
    escudo_interno = cv2.erode(escudo, np.ones((15, 15), np.uint8), iterations=1)

    if tipo_corte == TipoCorte.CONSERVAR:      # solo color/textura: cabello actual con margen suave
        zona = cv2.dilate(mascara, np.ones((11, 11), np.uint8))
    elif tipo_corte == TipoCorte.LARGO:        # el cabello crece: caída lateral en herradura hacia hombros
        zona = cv2.dilate(mascara, np.ones((25, 25), np.uint8))
        fy, fx = np.where(escudo_interno > 0)
        ys, xs = np.where(mascara > 0)
        caja = np.zeros_like(mascara)
        if len(fx):
            ancho = fx.max() - fx.min()
            alto = fy.max() - fy.min()
            cx = (fx.min() + fx.max()) // 2
            x0 = max(0, int(fx.min() - ancho * 0.80))
            x1 = min(w, int(fx.max() + ancho * 0.80))
            y0 = max(0, int((ys.min() if len(ys) else fy.min()) - h * 0.06))
            y1 = min(h, int(fy.max() + alto * 1.30))
            caja[y0:y1, x0:x1] = 255
            # Deja libre el centro del cuello/pecho debajo del mentón para que el pelo caiga a los lados
            cuello_y0 = min(h, int(fy.max() + alto * 0.12))
            cuello_x0 = max(0, int(cx - ancho * 0.28))
            cuello_x1 = min(w, int(cx + ancho * 0.28))
            caja[cuello_y0:y1, cuello_x0:cuello_x1] = 0
        elif len(xs):
            x0, x1 = max(0, int(xs.min() - w * 0.15)), min(w, int(xs.max() + w * 0.15))
            caja[max(0, int(ys.min() - h * 0.05)):min(h, int(ys.max() + h * 0.35)), x0:x1] = 255
        zona = np.maximum(zona, caja)
    elif tipo_corte == TipoCorte.MEDIO:
        zona = cv2.dilate(mascara, np.ones((39, 31), np.uint8))
    else:                                       # corto o calvo: cubre todo el pelo largo para borrarlo
        zona = cv2.dilate(mascara, np.ones((35, 35), np.uint8))

    return cv2.bitwise_and(zona, cv2.bitwise_not(escudo_interno))


def preparar_lienzo_corte(bgr: np.ndarray, mascara_pelo: np.ndarray, escudo: np.ndarray,
                          tipo_corte: TipoCorte) -> np.ndarray:
    """Borra el cabello largo previo antes de enviar a Colab cuando se pide un corte corto o calvo."""
    if tipo_corte not in (TipoCorte.CORTO, TipoCorte.MEDIO, TipoCorte.CALVO):
        return bgr
    escudo_interno = cv2.erode(escudo, np.ones((15, 15), np.uint8), iterations=1)
    a_borrar = cv2.dilate(mascara_pelo, np.ones((15, 15), np.uint8))
    a_borrar = cv2.bitwise_and(a_borrar, cv2.bitwise_not(escudo_interno))
    fy = np.where(escudo_interno > 0)[0]
    if len(fy) and tipo_corte == TipoCorte.MEDIO:
        corte_y = int(fy.max() + (fy.max() - fy.min()) * 0.15)
        a_borrar[:corte_y, :] = 0
    return cv2.inpaint(bgr, a_borrar, inpaintRadius=7, flags=cv2.INPAINT_TELEA)

def caja_recorte(zona: np.ndarray, margen: float = 0.15) -> tuple[int, int, int, int]:
    """Recorte cuadrado alrededor de la zona a editar: el modelo trabaja a 512 px sin deformar la foto."""
    h, w = zona.shape[:2]
    ys, xs = np.where(zona > 0)
    if not len(xs):
        return 0, 0, w, h
    bw, bh = xs.max() - xs.min(), ys.max() - ys.min()
    lado = int(max(bw, bh) * (1 + 2 * margen))
    cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    lw, lh = min(lado, w), min(lado, h)
    x0 = int(np.clip(cx - lw // 2, 0, w - lw))
    y0 = int(np.clip(cy - lh // 2, 0, h - lh))
    return x0, y0, x0 + lw, y0 + lh


def a_tamano_modelo(img: np.ndarray, es_mascara: bool = False) -> np.ndarray:
    """Lado mayor = 512 y ambos lados múltiplos de 8 (requisito de Stable Diffusion)."""
    h, w = img.shape[:2]
    escala = LADO_MODELO / max(h, w)
    nw, nh = max(8, int(w * escala) // 8 * 8), max(8, int(h * escala) // 8 * 8)
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_NEAREST if es_mascara else cv2.INTER_AREA)


def pegar(base: np.ndarray, parche: np.ndarray, caja: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = caja
    out = base.copy()
    out[y0:y1, x0:x1] = cv2.resize(parche, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
    return out


def suavizar(zona: np.ndarray) -> np.ndarray:
    return cv2.GaussianBlur(zona.astype(np.float32) / 255.0, (0, 0), 3.0)


def mezclar(orig: np.ndarray, gen: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    gen = cv2.resize(gen, (orig.shape[1], orig.shape[0]))
    a = np.clip((alpha - 0.05) / 0.9, 0, 1)[..., None]
    return np.clip(orig.astype(np.float32) * (1 - a) + gen.astype(np.float32) * a, 0, 255).astype(np.uint8)


def recolorear(bgr: np.ndarray, mascara: np.ndarray, hex_color: str, degradado: bool = False) -> np.ndarray:
    """Tinte en espacio LAB: conserva textura y brillos; con degradado, raíces más naturales."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    obj = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    cabello = mascara > 0
    if not np.any(cabello):
        return bgr
    L = lab[..., 0]
    base = cv2.GaussianBlur(L, (0, 0), 3.0)
    detalle = L - base
    L2 = np.clip(obj[0] + (base - base[cabello].mean()) * 0.85 + detalle * 1.15, 15, 245)
    brillo = np.clip((L2 - 185.0) / 60.0, 0, 1)
    peso = 0.92 * (1 - 0.35 * brillo)
    a2 = lab[..., 1] * (1 - peso) + obj[1] * peso
    b2 = lab[..., 2] * (1 - peso) + obj[2] * peso
    out = cv2.cvtColor(np.clip(np.dstack([L2, a2, b2]), 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    if degradado:
        ys = np.where(cabello)[0]
        t = np.clip((np.arange(bgr.shape[0], dtype=np.float32) - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)
        k = (0.30 + 0.70 * t * t * (3 - 2 * t))[:, None, None]
        out = (bgr.astype(np.float32) * (1 - k) + out.astype(np.float32) * k).astype(np.uint8)
    return out