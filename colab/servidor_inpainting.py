# LookFirst · Servidor de inpainting para Google Colab (GPU T4)
# 1) Entorno de ejecución > Cambiar tipo de entorno de ejecución > GPU T4
# 2) Pega TODO este archivo en una celda y ejecútala
# 3) Copia la URL que imprime al final en backend/.env como COLAB_URL (cambia en cada ejecución)
#
# Si Colab se desconectó: Entorno de ejecución > Reiniciar sesión, y vuelve a ejecutar la celda.

!pip install -q diffusers transformers accelerate fastapi uvicorn python-multipart pillow
!test -f cloudflared || (wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared)
# Limpia restos de una ejecución anterior (túnel viejo o servidor ocupando el puerto)
!pkill -f cloudflared || true
!fuser -k 8001/tcp 2>/dev/null || true

import io, re, subprocess, threading, time, torch, uvicorn, urllib.request
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image
from diffusers import DPMSolverMultistepScheduler, StableDiffusionInpaintPipeline

# --- 1. GPU ---
if not torch.cuda.is_available():
    raise SystemExit("❌ No hay GPU. Ve a Entorno de ejecución > Cambiar tipo de entorno > GPU T4 y vuelve a ejecutar. "
                     "Si no aparece la T4, se agotó la cuota gratuita de hoy: prueba con otra cuenta de Google o más tarde.")
print("✅ GPU:", torch.cuda.get_device_name(0))

# --- 2. Modelo (el repositorio original de runwayml fue retirado; se usa el espejo oficial) ---
pipe = None
for repo in ("stable-diffusion-v1-5/stable-diffusion-inpainting", "runwayml/stable-diffusion-inpainting"):
    try:
        pipe = StableDiffusionInpaintPipeline.from_pretrained(repo, torch_dtype=torch.float16, safety_checker=None).to("cuda")
        print("✅ Modelo:", repo)
        break
    except Exception as e:
        print(f"⚠️ No se pudo cargar {repo}: {type(e).__name__}: {str(e)[:150]}")
if pipe is None:
    raise SystemExit("❌ No se pudo descargar el modelo. Revisa la conexión de Colab y vuelve a ejecutar.")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
pipe.set_progress_bar_config(disable=True)
lock = threading.Lock()  # una GPU: una generación a la vez


def multiplo8(img):
    w, h = img.size
    return img.resize((max(8, w // 8 * 8), max(8, h // 8 * 8)))


def generar(img, msk, prompt, negative, steps):
    img, msk = multiplo8(img), multiplo8(msk)
    with lock, torch.inference_mode():
        return pipe(prompt=prompt, negative_prompt=negative, image=img, mask_image=msk,
                    width=img.width, height=img.height, num_inference_steps=steps, guidance_scale=7.5).images[0]


app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True, "gpu": torch.cuda.get_device_name(0)}


@app.post("/inpaint")
async def inpaint(image: UploadFile = File(...), mask: UploadFile = File(...), prompt: str = Form(...),
                  negative_prompt: str = Form("deformed face, blurry, cartoon, text"), steps: int = Form(15)):
    orig = Image.open(io.BytesIO(await image.read())).convert("RGB")
    msk = Image.open(io.BytesIO(await mask.read())).convert("L").resize(orig.size)
    out = generar(orig, msk, prompt, negative_prompt, max(8, min(steps, 30)))
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=92)
    return Response(content=buf.getvalue(), media_type="image/jpeg")


print("Calentando el modelo…")
generar(Image.new("RGB", (512, 512), "gray"), Image.new("L", (512, 512), 255), "short hair", "", 8)

# --- 3. Servidor local ---
servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="warning"))
threading.Thread(target=servidor.run, daemon=True).start()
for _ in range(30):
    try:
        urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=1)
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("❌ El servidor no arrancó en el puerto 8001. Reinicia la sesión (Entorno de ejecución > Reiniciar sesión) y vuelve a ejecutar.")
print("✅ Servidor listo")

# --- 4. Túnel público ---
tunnel = subprocess.Popen(["./cloudflared", "tunnel", "--url", "http://127.0.0.1:8001"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
url, ultimas, inicio = None, [], time.time()
for line in tunnel.stdout:
    ultimas = (ultimas + [line.strip()])[-8:]
    m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if m:
        url = m.group(0)
        break
    if time.time() - inicio > 60:
        break
if url:
    print("\n COPIA ESTA URL EN backend/.env COMO COLAB_URL:\n", url)
    print(" (Deja esta pestaña abierta mientras uses la app)")
else:
    print("❌ Cloudflare no devolvió una URL. Últimos mensajes del túnel:\n", "\n".join(ultimas))
    print("Vuelve a ejecutar la celda; si persiste, espera un minuto (Cloudflare limita túneles seguidos).")
