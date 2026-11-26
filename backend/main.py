import base64, io, json, os, re, threading, time, urllib.request, uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
TEMP, MODELS = BASE / "temp", BASE / "models"
HAIR_URL = "https://storage.googleapis.com/mediapipe-models/image_segmenter/hair_segmenter/float32/latest/hair_segmenter.tflite"
FACE_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
HAIR_PATH, FACE_PATH = MODELS / "hair_segmenter.tflite", MODELS / "face_landmarker.task"
MAX_SIDE = 896
LATENCY_BUDGET = float(os.getenv("LATENCY_BUDGET", "12.0"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "4.0"))
SID_RE = re.compile(r"^[a-f0-9]{32}$")
CATALOGO = json.loads((BASE / "catalogo_salon.json").read_text(encoding="utf-8"))

_lock = threading.RLock()  
_pool = ThreadPoolExecutor(max_workers=2)
_seg = _lmk = None


#modelos
def ensure_model(url: str, path: Path) -> Path:
    """Descarga el modelo la primera vez que se necesita."""
    if path.exists() and path.stat().st_size > 0:
        return path
    MODELS.mkdir(exist_ok=True)
    print(f"[LookFirst] Descargando {path.name} ...")
    tmp = path.with_suffix(path.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(path)
    return path


def segmenter():
    global _seg
    with _lock:
        if _seg is None:
            opts = vision.ImageSegmenterOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(ensure_model(HAIR_URL, HAIR_PATH))),
                running_mode=vision.RunningMode.IMAGE, output_category_mask=True,
                output_confidence_masks=True)
            _seg = vision.ImageSegmenter.create_from_options(opts)
        return _seg


def landmarker():
    global _lmk
    with _lock:
        if _lmk is None:
            opts = vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(ensure_model(FACE_URL, FACE_PATH))),
                running_mode=vision.RunningMode.IMAGE, num_faces=1)
            _lmk = vision.FaceLandmarker.create_from_options(opts)
        return _lmk


@asynccontextmanager
async def lifespan(_: FastAPI):
    TEMP.mkdir(exist_ok=True)
    clear_temp()  # nada de sesiones anteriores
    segmenter(); landmarker()  # descarga y precarga 
    yield


app = FastAPI(title="LookFirst API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def clear_temp() -> int:
    n = 0
    for f in TEMP.glob("*"):
        if f.is_file() and f.name != ".gitkeep":
            f.unlink(missing_ok=True); n += 1
    return n


def mp_image(bgr):
    rgb = np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)


#visión
def detect_face_shape(bgr):
    with _lock:
        res = landmarker().detect(mp_image(bgr))
    if not res.face_landmarks:
        raise HTTPException(422, "No se detectó ningún rostro. Mira de frente a la cámara con buena luz.")
    lm, (h, w) = res.face_landmarks[0], bgr.shape[:2]
    P = lambda i: np.array([lm[i].x * w, lm[i].y * h])
    d = lambda a, b: float(np.linalg.norm(P(a) - P(b)))
    cheek, jaw, fore, height = d(234, 454), d(172, 397), d(54, 284), d(10, 152)
    hw, jr, fr = height / cheek, jaw / cheek, fore / cheek
    # Heurística de visagismo basada en proporciones de landmarks
    if hw >= 1.40:
        forma = "alargado"
    elif hw < 1.25:
        forma = "cuadrado" if jr >= 0.82 else "redondo"
    else:
        forma = "cuadrado" if jr >= 0.86 else "ovalado"
    return forma, {"alto_ancho": round(hw, 2), "mandibula_pomulos": round(jr, 2), "frente_pomulos": round(fr, 2)}


def hair_mask(bgr):
    """Devuelve (mask, soft): mask binaria estricta (255 = cabello) y matte suave 0..1 con la confianza del modelo."""
    with _lock:
        res = segmenter().segment(mp_image(bgr))
    h, w = bgr.shape[:2]
    mask = (res.category_mask.numpy_view() == 1).astype(np.uint8) * 255
    if mask.shape[:2] != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = (mask > 127).astype(np.uint8) * 255
    if mask.mean() / 255 < 0.005:
        raise HTTPException(422, "No se detectó cabello en la imagen.")
    confs = res.confidence_masks or []
    conf = np.array(confs[1].numpy_view(), dtype=np.float32) if len(confs) > 1 else mask.astype(np.float32) / 255
    if conf.shape[:2] != (h, w):
        conf = cv2.resize(conf, (w, h), interpolation=cv2.INTER_LINEAR)
    soft = cv2.GaussianBlur(np.clip(conf, 0, 1), (0, 0), 1.0)
    soft *= (cv2.dilate(mask, np.ones((7, 7), np.uint8)) > 0)  # el matte nunca sale de la zona de cabello
    return mask, soft


def blend(orig, gen, alpha):
    """Mezcla con matte suave (probabilidad del segmentador): conserva mechones finos en el borde."""
    gen = cv2.resize(gen, (orig.shape[1], orig.shape[0]))
    a = np.clip((alpha - 0.05) / 0.9, 0, 1)[..., None]
    out = orig.astype(np.float32) * (1 - a) + gen.astype(np.float32) * a
    return np.clip(out, 0, 255).astype(np.uint8)


def recolor_fallback(bgr, mask, hex_color, ombre=False):
    """Tinte realista en LAB: conserva textura de mechones y brillos, y aplica degradado raíz→puntas (ombré/balayage)."""
    if not hex_color:
        return bgr.copy()
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    tgt = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    hair = mask > 0
    L = lab[..., 0]
    base = cv2.GaussianBlur(L, (0, 0), 3.0)          # tono/sombras de la melena (baja frecuencia)
    detail = L - base                                 # textura de mechones (alta frecuencia)
    mu = base[hair].mean()
    base2 = tgt[0] + (base - mu) * 0.9                # mueve el tono medio al objetivo conservando el volumen
    L2 = np.clip(base2 + detail * 1.15, 0, 255)       # realza un poco los mechones
    hi = np.clip((L2 - 170.0) / 60.0, 0, 1)           # en los brillos el color se desatura (reflejo)
    w = 0.88 * (1 - 0.5 * hi)
    a2 = lab[..., 1] * (1 - w) + tgt[1] * w
    b2 = lab[..., 2] * (1 - w) + tgt[2] * w
    out = cv2.cvtColor(np.clip(np.dstack([L2, a2, b2]), 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    if ombre:  # raíces más naturales, puntas con el color completo
        ys = np.where(hair)[0]
        t = np.clip((np.arange(bgr.shape[0], dtype=np.float32) - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)
        amt = (0.35 + 0.65 * t * t * (3 - 2 * t))[:, None, None]
        out = (bgr.astype(np.float32) * (1 - amt) + out.astype(np.float32) * amt).astype(np.uint8)
    return out


def colab_inpaint(bgr, mask, prompt, timeout):
    """Inpainting real en GPU T4 gratuita de Google Colab. Devuelve None si falla."""
    url = os.getenv("COLAB_URL", "").rstrip("/")
    if not url or timeout < 1.5:
        return None
    try:
        ok_img, buf_img = cv2.imencode(".png", bgr)
        ok_msk, buf_msk = cv2.imencode(".png", mask)
        if not (ok_img and ok_msk):
            return None
        r = requests.post(
            f"{url}/inpaint",
            files={"image": ("img.png", buf_img.tobytes(), "image/png"),
                   "mask": ("mask.png", buf_msk.tobytes(), "image/png")},
            data={"prompt": prompt},
            timeout=timeout,
        )
        if r.status_code == 200:
            return cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        print("[Colab] error HTTP:", r.status_code, r.text[:120])
    except Exception as e:
        print("[Colab] error:", e)
    return None


#LLM
SYSTEM = (
    "You are a senior hair stylist assistant. Convert the client's colloquial Spanish request into a technical "
    "English prompt for Stable Diffusion Inpainting that edits ONLY the head/hair area. Respond with ONLY valid JSON: "
    '{"prompt_en": "...", "color_hex": "#RRGGBB or null", "cut_type": "bald|short|medium|long"}. '
    "Rules for prompt_en (<=35 words): "
    "1) If bald/shaved ('calvo', 'rapado', 'pelado'), describe 'completely bald person, cleanly shaved smooth scalp, natural skin texture matching face, salon lighting' and DO NOT use the words 'hair' or 'hair texture'. "
    "2) Otherwise, describe specific haircut length, shape, color, and include 'realistic hair texture, natural salon lighting'. "
    "Rules for cut_type: 'bald' for shaved head, 'short' for pixie/buzz/fade/short cuts, 'medium' for bob/lob/shoulder-length/bangs, 'long' for long hair/waves/layers past shoulders. "
    "Rules for color_hex: dominant target hair color in #RRGGBB format, or null if bald or no color change is requested."
    "When a vivid or fantasy hair color is requested (pink, purple, violet, green, blue, red, platinum), reinforce the prompt with 'vibrant dyed  hair, saturated salon hair dye, fully colored strands' so dark hair is completely recolored."
)
COLORS = [
    # Rubios (específicos primero)
    ("rubio platin", "platinum blonde", "#E6DFD3"),
    ("platinado", "platinum blonde", "#E6DFD3"),
    ("rubio ceniza", "ash blonde", "#BDB2A0"),
    ("ceniza", "ash blonde", "#BDB2A0"),
    ("rubio miel", "honey blonde", "#C99E59"),
    ("miel", "honey blonde", "#C99E59"),
    ("rubio dorado", "golden blonde", "#D4B06A"),
    ("rubio oscuro", "dark dirty blonde", "#8C7355"),
    ("rubio", "golden blonde", "#D4B06A"),
    # Cobrizos y rojos
    ("cobrizo", "warm copper", "#B4592B"),
    ("cobre", "warm copper", "#B4592B"),
    ("caoba", "mahogany auburn", "#6E2622"),
    ("pelirroj", "vibrant ginger red", "#A8321E"),
    ("borgo", "deep burgundy", "#6B1D2F"),
    ("burdeos", "deep burgundy", "#6B1D2F"),
    ("vino", "wine red", "#6B1D2F"),
    ("rojo", "vibrant red", "#B3202A"),
    # Castaños y negros
    ("castaño claro", "light caramel brown", "#7C5638"),
    ("castaño oscuro", "dark espresso brown", "#2E1D16"),
    ("chocolate", "rich chocolate brown", "#4B2E22"),
    ("caramelo", "caramel brown", "#8E5B37"),
    ("casta", "chestnut brown", "#5A3A28"),
    ("marrón", "chestnut brown", "#5A3A28"),
    ("negro azulado", "blue-black", "#11141D"),
    ("negro", "jet black", "#16110F"),
    # Fantasía y platinados
    ("rosa pastel", "pastel pink", "#E59AB0"),
    ("fucsia", "vibrant magenta pink", "#C2276B"),
    ("rosa", "pastel pink", "#E59AB0"),
    ("morado", "deep violet purple", "#5A2D82"),
    ("violeta", "lavender violet", "#8868A8"),
    ("lila", "pastel lilac", "#B49AC9"),
    ("azul", "midnight blue", "#2C5AA0"),
    ("turquesa", "teal turquoise", "#25898E"),
    ("verde", "emerald green", "#236B48"),
    ("plate", "silver gray", "#B9BCC2"),
    ("canas", "natural salt and pepper gray", "#9EA2A8"),
    ("gris", "silver gray", "#B9BCC2"),
]
CUT_PROFILES = [
    (("calvo", "rapado", "pelado", "sin pelo"), "bald",
     "completely bald person, cleanly shaved smooth scalp, natural skin texture matching face"),
    (("buzz", "al cero", "militar"), "short",
     "ultra short buzz cut hairstyle, clean fade on sides, natural scalp and short hair texture"),
    (("pixie", "duendecillo", "muy corto"), "short",
     "chic textured pixie haircut, short cropped layered hair around ears and nape"),
    (("bob", "carré", "melena corta"), "medium",
     "classic chin-length layered bob haircut framing the jawline, smooth natural hair"),
    (("lob", "long bob", "media melena"), "medium",
     "shoulder-length wavy long bob haircut, textured ends, natural volume"),
    (("flequillo", "cerquillo", "bangs"), "medium",
     "hairstyle with soft curtain bangs framing the forehead and cheekbones"),
    (("capas", "degrafilado", "layered"), "long",
     "long layered haircut falling past the shoulders with face-framing layers and volume"),
    (("ondas", "ondulado", "rizos", "waves"), "long",
     "long flowing wavy hair falling over the shoulders, soft voluminous curls"),
    (("largo", "melena larga", "long hair"), "long",
     "long straight silky hair extending down past the shoulders, natural shine"),
    (("corto", "degradado", "fade"), "short",
     "modern short tapered men's haircut, textured top and clean faded sides"),
]

def detect_cut_type(texto: str) -> str:
    t = texto.lower()
    for keys, ctype, _ in CUT_PROFILES:
        if any(k in t for k in keys):
            return ctype
    if any(w in t for w in ("long", "shoulder", "waves", "curls", "layers")):
        return "long"
    if any(w in t for w in ("bob", "lob", "bangs", "chin")):
        return "medium"
    return "short"

def get_face_shield(bgr, pad_px: int = 0):
    """Protege estrictamente las facciones interiores sin invadir la línea del cabello ni patillas."""
    h, w = bgr.shape[:2]
    shield = np.zeros((h, w), dtype=np.uint8)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    detector = landmarker() if callable(landmarker) else landmarker
    res = detector.detect(mp_img)
    if res.face_landmarks:
        pts = np.array(
            [[int(lm.x * w), int(lm.y * h)] for lm in res.face_landmarks[0]],
            dtype=np.int32,
        )
        hull = cv2.convexHull(pts)
        cv2.fillConvexPoly(shield, hull, 255)
        #4px el borde superior del óvalo para liberar flequillo, entradas y patillas
        shield = cv2.erode(shield, np.ones((9, 9), np.uint8), iterations=1)
    return shield

def build_cut_mask(mask, cut_type: str, bgr=None):
    """Adapta la máscara según el corte y blinda las facciones sin bloquear raíces ni patillas."""
    h, w = mask.shape[:2]
    face_shield = get_face_shield(bgr) if bgr is not None else np.zeros_like(mask)

    if cut_type == "long":
        long_zone = np.zeros_like(mask)
        fy, fx = np.where(face_shield > 0)
        ys, xs = np.where(mask > 0)

        if len(fx) > 0:
            face_w = fx.max() - fx.min()
            x_min = max(0, int(fx.min() - face_w * 0.65))
            x_max = min(w, int(fx.max() + face_w * 0.65))
            y_top = max(0, int((ys.min() if len(ys) else fy.min()) - h * 0.04))
            y_bot = min(h, int(fy.max() + (fy.max() - fy.min()) * 1.15))
            long_zone[y_top:y_bot, x_min:x_max] = 255
        elif len(xs) > 0:
            x_min, x_max = max(0, int(xs.min() - w * 0.12)), min(w, int(xs.max() + w * 0.12))
            y_top = max(0, int(ys.min() - h * 0.04))
            y_bot = min(h, int(ys.max() + h * 0.35))
            long_zone[y_top:y_bot, x_min:x_max] = 255

        work = np.maximum(cv2.dilate(mask, np.ones((21, 21), np.uint8)), long_zone)
    elif cut_type == "medium":
        work = cv2.dilate(mask, np.ones((35, 25), np.uint8), iterations=1)
    else:
        work = cv2.dilate(mask, np.ones((25, 25), np.uint8), iterations=1)

    work = cv2.bitwise_and(work, cv2.bitwise_not(face_shield))
    return work

def keyword_translate(texto):
    t = texto.lower()
    color = next(((en, hx) for k, en, hx in COLORS if k in t), (None, None))
    cut_match = next(((ctype, en) for keys, ctype, en in CUT_PROFILES if any(k in t for k in keys)), None)

    if cut_match and cut_match[0] == "bald":
        return f"professional portrait photo of a {cut_match[1]}, realistic salon lighting, high detail", None

    cut_desc = cut_match[1] if cut_match else "stylish modern haircut"
    color_desc = f"with vibrant dyed {color[0]} hair, saturated salon hair color" if color[0] else "with natural hair color"
    prompt = f"professional salon portrait photo of a person with {cut_desc} {color_desc}, realistic hair texture, high detail"
    return prompt, color[1]


def _llm_call(texto):
    if os.getenv("GEMINI_API_KEY"):
        from google import genai
        c = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        txt = c.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=f"{SYSTEM}\nClient request: {texto}"
        ).text
    elif os.getenv("GROQ_API_KEY"):
        from groq import Groq
        r = Groq(api_key=os.environ["GROQ_API_KEY"]).chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": texto}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        txt = r.choices[0].message.content
    else:
        return None
    data = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
    hx = data.get("color_hex")
    valid_hx = hx if isinstance(hx, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", hx) else None
    ctype = data.get("cut_type")
    valid_ctype = ctype if ctype in ("bald", "short", "medium", "long") else detect_cut_type(f"{texto} {data['prompt_en']}")
    return data["prompt_en"], valid_hx, valid_ctype


def translate_request(texto):
    """LLM con timeout; si falla, traducción por palabras clave. Devuelve (prompt, hex, cut_type, fuente)."""
    try:
        out = _pool.submit(_llm_call, texto).result(timeout=LLM_TIMEOUT)
        if out:
            return out[0], out[1], out[2], "llm"
    except (FutureTimeout, Exception) as e:
        print("[LLM] respaldo por palabras clave:", e)
    p, hx = keyword_translate(texto)
    return p, hx, detect_cut_type(texto), "keywords"


#endpoints
def recommend(forma):
    ok = [s for s in CATALOGO if forma in s["formas"]]
    ok += [s for s in CATALOGO if s not in ok]
    return ok[:3]


@app.get("/health")
def health():
    return {"ok": True, "hf": bool(os.getenv("HF_TOKEN")),
            "llm": "gemini" if os.getenv("GEMINI_API_KEY") else "groq" if os.getenv("GROQ_API_KEY") else "keywords"}


@app.post("/analyze-face")
def analyze_face(file: UploadFile = File(...)):
    raw = file.file.read()
    if not raw or len(raw) > 12 * 1024 * 1024:
        raise HTTPException(400, "Imagen vacía o demasiado grande (máx. 12 MB).")
    try:
        pil = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except Exception:
        raise HTTPException(400, "El archivo no es una imagen válida.")
    pil.thumbnail((MAX_SIDE, MAX_SIDE))
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    forma, metricas = detect_face_shape(bgr)
    sid = uuid.uuid4().hex
    cv2.imwrite(str(TEMP / f"{sid}.jpg"), bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return {"session_id": sid, "forma_rostro": forma, "metricas": metricas, "recomendaciones": recommend(forma)}


@app.post("/simulate")
def simulate(session_id: str = Form(...), instruccion: str = Form(""), estilo_id: str = Form("")):
    t0 = time.perf_counter()
    if not SID_RE.match(session_id) or not (TEMP / f"{session_id}.jpg").exists():
        raise HTTPException(404, "Sesión no encontrada. Captura o sube una foto de nuevo.")
    
    bgr = cv2.imread(str(TEMP / f"{session_id}.jpg"))
    mask, soft = hair_mask(bgr)
    cv2.imwrite(str(TEMP / f"{session_id}_mask.png"), mask)

    estilo = next((s for s in CATALOGO if s["id"] == estilo_id), None)
    if estilo:
        prompt, color, fuente = estilo["prompt_en"], estilo["color_hex"], "catalogo"
        cut_type = detect_cut_type(f"{estilo_id} {prompt}")
    elif instruccion.strip():
        prompt, color, cut_type, fuente = translate_request(instruccion.strip())
    else:
        raise HTTPException(400, "Indica un estilo del catálogo o una instrucción.")

    # Ajusta la geometría de la máscara según el tipo de corte (bald, short, medium, long)
    work_mask = build_cut_mask(mask, cut_type, bgr)
    cv2.imwrite(str(TEMP / f"{session_id}_work_mask.png"), work_mask)

    restante = LATENCY_BUDGET - (time.perf_counter() - t0) - 0.5  # reserva para blending/codificación
    gen = colab_inpaint(bgr, work_mask, prompt, restante)
    modo = "colab-inpainting" if gen is not None else "respaldo-opencv"

    if gen is not None:
        # Suaviza la máscara expandida para integrar cortes nuevos o calvicie sin recortar con la silueta vieja
        soft_final = cv2.GaussianBlur(work_mask.astype(np.float32) / 255.0, (0, 0), 3.0)
        out = blend(bgr, gen, soft_final)
    else:
        ombre = "balayage" in estilo_id or any(k in instruccion.lower() for k in ("balayage", "degrad", "ombre", "ombré"))
        gen = recolor_fallback(bgr, mask, color, ombre)
        out = blend(bgr, gen, soft)

    cv2.imwrite(str(TEMP / f"{session_id}_result.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    img_b64 = base64.b64encode(cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()).decode()
    
    aviso = None
    if modo == "respaldo-opencv" and not color:
        aviso = "El modo de respaldo solo cambia el color; el cambio de corte requiere la conexión activa con Colab."
        
    return {
        "imagen_b64": img_b64,
        "latencia_s": round(time.perf_counter() - t0, 2),
        "modo": modo,
        "cut_type": cut_type,
        "prompt_en": prompt,
        "fuente_prompt": fuente,
        "aviso": aviso,
    }


@app.post("/cleanup")
def cleanup():
    n = clear_temp()
    return {"ok": True, "eliminados": n, "restantes": len([f for f in TEMP.glob("*") if f.name != ".gitkeep"])}
