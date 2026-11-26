"""Configuración leída del entorno (.env). Único lugar donde se tocan variables de entorno."""
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def _float(nombre: str, defecto: float) -> float:
    return float(os.getenv(nombre, str(defecto)))


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/lookfirst"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET") or secrets.token_urlsafe(32))
    jwt_horas: int = field(default_factory=lambda: int(os.getenv("JWT_HORAS", "10")))

    admin_nombre: str = field(default_factory=lambda: os.getenv("ADMIN_NOMBRE", "Administrador del salón"))
    admin_email: str = field(default_factory=lambda: os.getenv("ADMIN_EMAIL", ""))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", ""))

    colab_url: str = field(default_factory=lambda: os.getenv("COLAB_URL", "").rstrip("/"))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    # REQ-04: la simulación completa debe responder en <= 6 s
    latency_budget: float = field(default_factory=lambda: _float("LATENCY_BUDGET", 6.0))
    llm_timeout: float = field(default_factory=lambda: _float("LLM_TIMEOUT", 2.5))
    # REQ-09: tiempo máximo que una foto vive en memoria si nadie finaliza la consulta
    ttl_foto_min: int = field(default_factory=lambda: int(os.getenv("TTL_FOTO_MIN", "30")))
    # OE4: tiempo de decisión medido con el método tradicional (para calcular la reducción)
    tiempo_decision_tradicional_min: float = field(default_factory=lambda: _float("TIEMPO_DECISION_TRADICIONAL_MIN", 0))

    cors_origins: tuple[str, ...] = field(default_factory=lambda: tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200").split(",") if o.strip()))
    models_dir: Path = BACKEND_DIR / "models"
    catalogo_semilla: Path = BACKEND_DIR / "catalogo_salon.json"

    @property
    def jwt_secret_generado(self) -> bool:
        return not os.getenv("JWT_SECRET")
