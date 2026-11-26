const API = "http://localhost:8000";
const $ = (id) => document.getElementById(id);
const state = { stream: null, sid: null, beforeURL: null, consent: false, busy: false };
const SIM_LIMIT_S = 6;

function status(msg, kind = "") {
  const el = $("status");
  el.textContent = msg;
  el.className = "mt-3 min-h-[1.5rem] font-medium " + (kind === "ok" ? "text-ok" : kind === "err" ? "text-warn" : "");
}
function view(v) { // empty | video | photo | result
  $("video").classList.toggle("hidden", v !== "video");
  $("photo").classList.toggle("hidden", v !== "photo");
  $("compare").classList.toggle("hidden", v !== "result");
  $("empty").classList.toggle("hidden", v !== "empty");
  $("btn-retake").classList.toggle("hidden", !["photo", "result"].includes(v));
  $("btn-capture").disabled = !(state.consent && v === "video");
}
function busy(on, text = "Procesando…") {
  state.busy = on;
  $("loading").classList.toggle("hidden", on ? false : true);
  $("loading").classList.toggle("flex", on);
  $("loading-text").textContent = text;
  ["btn-go", "btn-mic"].forEach((id) => ($(id).disabled = on || !state.sid));
}
function enableControls(on) {
  $("file").disabled = !on;
  $("upload-label").classList.toggle("opacity-40", !on);
  $("text").disabled = !on || !state.sid;
  $("btn-go").disabled = !on || !state.sid;
  $("btn-mic").disabled = !on || !state.sid;
}

/* ---------- Consentimiento ---------- */
function openConsent() { $("consent").classList.remove("hidden"); $("consent-check").checked = false; $("consent-yes").disabled = true; }
$("consent-check").onchange = (e) => ($("consent-yes").disabled = !e.target.checked);
$("consent-no").onclick = () => $("consent-msg").classList.remove("hidden");
$("consent-yes").onclick = async () => {
  state.consent = true;
  $("consent").classList.add("hidden");
  enableControls(true);
  await startCamera();
};
$("btn-start").onclick = openConsent;

/* ---------- Cámara (WebRTC) ---------- */
async function startCamera() {
  if (!state.consent) return;
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false });
    $("video").srcObject = state.stream;
    view("video");
    status("Cámara lista. Mira de frente y pulsa «Capturar foto».");
  } catch (e) {
    view("empty");
    status("No se pudo acceder a la cámara. Revisa los permisos del navegador o sube una foto.", "err");
  }
}
function stopCamera() {
  state.stream?.getTracks().forEach((t) => t.stop());
  state.stream = null;
  $("video").srcObject = null;
}
$("btn-capture").onclick = () => {
  const v = $("video");
  const c = document.createElement("canvas");
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext("2d").drawImage(v, 0, 0);
  c.toBlob((blob) => analyze(blob), "image/jpeg", 0.92);
};
$("file").onchange = (e) => { const f = e.target.files[0]; if (f && state.consent) analyze(f); e.target.value = ""; };
$("btn-retake").onclick = async () => {
  state.sid = null; $("metrics").classList.add("hidden");
  $("shape").textContent = "Aún no analizado. Captura una foto para detectar tu forma de rostro.";
  $("styles").innerHTML = '<p class="text-ink/70">Aparecerán aquí tras el análisis.</p>';
  enableControls(true);
  stream_or_empty();
};
function stream_or_empty() { state.stream ? view("video") : startCamera(); }

/* ---------- Análisis ---------- */
async function analyze(blob) {
  if (state.busy) return;
  revoke();
  state.beforeURL = URL.createObjectURL(blob);
  $("photo").src = state.beforeURL;
  view("photo");
  busy(true, "Analizando tu rostro…");
  try {
    const fd = new FormData(); fd.append("file", blob, "captura.jpg");
    const r = await fetch(`${API}/analyze-face`, { method: "POST", body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Error al analizar la imagen");
    state.sid = data.session_id;
    $("shape").textContent = `Forma de rostro: ${data.forma_rostro} (alto/ancho ${data.metricas.alto_ancho}, mandíbula/pómulos ${data.metricas.mandibula_pomulos}).`;
    renderStyles(data.recomendaciones);
    enableControls(true);
    status("Listo. Elige un estilo, escribe o usa la voz.", "ok");
  } catch (e) {
    state.sid = null;
    status(e.message.includes("fetch") ? "No hay conexión con el servidor. ¿Está corriendo en el puerto 8000?" : e.message, "err");
    stream_or_empty();
  } finally { busy(false); }
}
function renderStyles(list) {
  const box = $("styles"); box.innerHTML = "";
  list.forEach((s) => {
    const b = document.createElement("button");
    b.className = "w-full text-left rounded-xl border border-mist p-4 hover:bg-paper flex gap-3 items-start";
    const sw = document.createElement("span");
    sw.className = "mt-1 h-6 w-6 rounded-full shrink-0 border border-ink/20";
    sw.style.background = s.color_hex || "linear-gradient(135deg,#3a3347,#8d7fb0)";
    const t = document.createElement("span");
    t.innerHTML = `<strong class="block"></strong><span class="text-sm text-ink/70 block"></span><span class="text-sm text-iris font-semibold"></span>`;
    t.children[0].textContent = s.nombre; t.children[1].textContent = s.descripcion; t.children[2].textContent = "Simular " + s.tipo;
    b.append(sw, t);
    b.onclick = () => simulate({ estilo_id: s.id });
    box.appendChild(b);
  });
}

/* ---------- Simulación ---------- */
async function simulate({ estilo_id = "", instruccion = "" }) {
  if (!state.sid || state.busy) return;
  busy(true, "Creando tu nuevo look…");
  try {
    const fd = new FormData();
    fd.append("session_id", state.sid); fd.append("estilo_id", estilo_id); fd.append("instruccion", instruccion);
    const r = await fetch(`${API}/simulate`, { method: "POST", body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "Error en la simulación");
    $("before").src = state.beforeURL;
    $("after").src = "data:image/jpeg;base64," + d.imagen_b64;
    $("range").value = 50; slider(50);
    view("result");
    const m = $("metrics"); m.classList.remove("hidden"); m.classList.add("flex");
    const ok = d.latencia_s <= SIM_LIMIT_S;
    m.innerHTML = `<span class="px-3 py-1.5 rounded-lg font-semibold ${ok ? "bg-ok/15 text-ok" : "bg-warn/15 text-warn"}">Simulado en ${d.latencia_s.toFixed(2)} s</span>
                   <span class="px-3 py-1.5 rounded-lg bg-mist">${d.modo === "hf-inpainting" ? "IA generativa" : "Modo respaldo local"}</span>`;
    status(d.aviso || `Prompt técnico: ${d.prompt_en}`, d.aviso ? "err" : "");
  } catch (e) {
    status(e.message.includes("fetch") ? "No hay conexión con el servidor." : e.message, "err");
  } finally { busy(false); }
}
$("btn-go").onclick = () => { const t = $("text").value.trim(); if (t) simulate({ instruccion: t }); else status("Escribe o di qué estilo quieres.", "err"); };
$("text").onkeydown = (e) => { if (e.key === "Enter") $("btn-go").click(); };

/* ---------- Comparador ---------- */
function slider(v) { $("before").style.clipPath = `inset(0 ${100 - v}% 0 0)`; $("handle").style.left = v + "%"; }
$("range").oninput = (e) => slider(+e.target.value);

/* ---------- Voz (es-PE) ---------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec = null;
$("btn-mic").onclick = () => {
  if (!SR) return status("Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge, o escribe la petición.", "err");
  if (rec) { rec.stop(); return; }
  rec = new SR(); rec.lang = "es-PE"; rec.interimResults = false; rec.maxAlternatives = 1;
  const set = (on) => { $("btn-mic").setAttribute("aria-pressed", on); $("mic-label").textContent = on ? "Escuchando… (toca para parar)" : "Hablar (español)"; $("btn-mic").classList.toggle("bg-iris", on); $("btn-mic").classList.toggle("text-white", on); };
  rec.onstart = () => set(true);
  rec.onresult = (e) => { const t = e.results[0][0].transcript; $("text").value = t; status(`Escuché: «${t}»`); simulate({ instruccion: t }); };
  rec.onerror = (e) => status(e.error === "not-allowed" ? "Permite el micrófono para usar comandos de voz." : "No te pude escuchar. Inténtalo de nuevo.", "err");
  rec.onend = () => { set(false); rec = null; };
  rec.start();
};

/* ---------- Finalizar y borrado biométrico ---------- */
function revoke() { if (state.beforeURL) URL.revokeObjectURL(state.beforeURL); state.beforeURL = null; }
$("btn-finish").onclick = async () => {
  try {
    const r = await fetch(`${API}/cleanup`, { method: "POST" });
    const d = await r.json();
    if (!r.ok || !d.ok) throw new Error();
    stopCamera(); revoke();
    ["photo", "before", "after"].forEach((id) => $(id).removeAttribute("src"));
    Object.assign(state, { sid: null, consent: false });
    $("metrics").classList.add("hidden");
    $("shape").textContent = "Aún no analizado. Captura una foto para detectar tu forma de rostro.";
    $("styles").innerHTML = '<p class="text-ink/70">Aparecerán aquí tras el análisis.</p>';
    $("text").value = "";
    enableControls(false); view("empty");
    status(`Consulta finalizada. Se eliminaron ${d.eliminados} archivo(s) temporales del servidor (${d.restantes} restantes) y se cerró la cámara.`, "ok");
  } catch {
    status("No se pudo confirmar el borrado. Verifica que el servidor esté activo y vuelve a intentarlo.", "err");
  }
};
window.addEventListener("pagehide", () => navigator.sendBeacon?.(`${API}/cleanup`)); // borrado al cerrar la pestaña

openConsent(); view("empty"); enableControls(false);
