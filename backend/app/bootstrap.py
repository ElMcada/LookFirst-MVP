"""Composition root: el único lugar que conoce las implementaciones concretas y las conecta."""
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.analitica.api.router import router as metricas_router
from app.catalogo.api.router import router as catalogo_router
from app.catalogo.application.servicio_catalogo import ServicioCatalogo
from app.catalogo.infrastructure.repositorio import RepositorioEstilosSQL
from app.consulta.api.router import construir_servicio
from app.consulta.api.router import router as consulta_router
from app.consulta.application.servicio_consulta import ServicioConsulta
from app.consulta.infrastructure.fotos_memoria import AlmacenFotosMemoria
from app.iam.api.router import router as iam_router
from app.iam.application.servicio_iam import ServicioIAM
from app.iam.infrastructure.repositorio import RepositorioUsuariosSQL
from app.iam.infrastructure.seguridad import EmisorJWT, HasherScrypt
from app.shared.config import Settings
from app.shared.db import asegurar_base_datos, crear_engine, crear_fabrica_sesiones, inicializar_esquema
from app.shared.errores import ErrorDominio
from app.simulacion.application.motor import MotorSimulacion

INTERVALO_PURGA_S = 60


def construir_motor(s: Settings) -> MotorSimulacion:
    from app.simulacion.infrastructure.inpainter_colab import InpainterColab
    from app.simulacion.infrastructure.interprete_llm import InterpreteGemini, InterpreteGroq
    from app.simulacion.infrastructure.interprete_palabras_clave import InterpretePalabrasClave
    from app.simulacion.infrastructure.vision_mediapipe import AnalizadorFacialMediaPipe, SegmentadorCabelloMediaPipe

    ia = None
    if s.gemini_api_key:
        ia = InterpreteGemini(s.gemini_api_key, s.gemini_model)
    elif s.groq_api_key:
        ia = InterpreteGroq(s.groq_api_key, s.groq_model)
    return MotorSimulacion(AnalizadorFacialMediaPipe(s.models_dir), SegmentadorCabelloMediaPipe(s.models_dir),
                           InpainterColab(s.colab_url), InterpretePalabrasClave(), ia, s.llm_timeout)


def _servicio_consulta(app: FastAPI, db) -> ServicioConsulta:
    return construir_servicio(app.state, db)


def _purgar(app: FastAPI) -> int:
    with app.state.fabrica_sesiones.begin() as db:
        return _servicio_consulta(app, db).expirar_vencidas(app.state.settings.ttl_foto_min * 60)


def _bucle_purga(app: FastAPI, parar: threading.Event) -> None:
    while not parar.wait(INTERVALO_PURGA_S):
        try:
            n = _purgar(app)
            if n:
                print(f"[LookFirst] {n} foto(s) vencida(s) eliminada(s) de memoria")
        except Exception as e:
            print("[LookFirst] error en la purga automática:", e)


def _sembrar(app: FastAPI) -> None:
    s = app.state.settings
    with app.state.fabrica_sesiones.begin() as db:
        n = ServicioCatalogo(RepositorioEstilosSQL(db)).sembrar_si_vacio(s.catalogo_semilla)
        if n:
            print(f"[LookFirst] Catálogo inicial cargado: {n} estilos")
        admin = ServicioIAM(RepositorioUsuariosSQL(db), HasherScrypt(), EmisorJWT(s.jwt_secret, s.jwt_horas)) \
            .asegurar_admin_inicial(s.admin_nombre, s.admin_email, s.admin_password)
        if admin:
            print(f"[LookFirst] Administrador inicial creado: {admin.email}")
        huerfanas = _servicio_consulta(app, db).expirar_huerfanas()
        if huerfanas:
            print(f"[LookFirst] {huerfanas} consulta(s) abiertas de una ejecución anterior marcadas como expiradas")


def create_app(settings: Settings | None = None, motor: MotorSimulacion | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.jwt_secret_generado:
            print("[LookFirst] AVISO: falta JWT_SECRET en .env; las sesiones se perderán al reiniciar.")
        asegurar_base_datos(settings.database_url)
        engine = crear_engine(settings.database_url)
        inicializar_esquema(engine)
        app.state.engine = engine
        app.state.fabrica_sesiones = crear_fabrica_sesiones(engine)
        app.state.fotos = AlmacenFotosMemoria()
        app.state.motor = motor or construir_motor(settings)
        _sembrar(app)
        parar = threading.Event()
        hilo = threading.Thread(target=_bucle_purga, args=(app, parar), daemon=True)
        hilo.start()
        yield
        parar.set()
        engine.dispose()

    app = FastAPI(title="LookFirst API", version="2.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"],
                       allow_headers=["*"])

    @app.exception_handler(ErrorDominio)
    async def _error_dominio(_: Request, exc: ErrorDominio):
        return JSONResponse({"detail": exc.mensaje}, status_code=exc.codigo_http)

    @app.get("/health", tags=["Sistema"])
    def health():
        try:
            with app.state.engine.connect() as c:
                c.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        llm = "gemini" if settings.gemini_api_key else "groq" if settings.groq_api_key else "palabras_clave"
        return {"ok": db_ok, "base_datos": db_ok, "llm": llm, "ia_generativa": bool(settings.colab_url),
                "presupuesto_latencia_s": settings.latency_budget, "fotos_en_memoria": len(app.state.fotos)}

    for r in (iam_router, catalogo_router, consulta_router, metricas_router):
        app.include_router(r)
    return app
