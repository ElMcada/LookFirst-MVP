"""Agregado Consulta: una atención en el sillón, desde el consentimiento hasta el borrado de la foto."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.shared.errores import Conflicto, EntradaInvalida, NoEncontrado, Prohibido
from app.shared.kernel import TipoCorte, ahora

VERSION_CONSENTIMIENTO = "2026-11-v1"   # cambia si cambia el texto legal mostrado al cliente
MAX_SIMULACIONES = 30                   # cuota por consulta (riesgo de costos de nube)


class EstadoConsulta(str, Enum):
    ACTIVA = "activa"
    FINALIZADA = "finalizada"   # el estilista la cerró
    CANCELADA = "cancelada"     # el cliente retiró su consentimiento
    EXPIRADA = "expirada"       # nadie la cerró y venció el tiempo de vida de la foto


class OrigenSolicitud(str, Enum):
    CATALOGO = "catalogo"
    TEXTO = "texto"
    VOZ = "voz"


@dataclass
class Simulacion:
    """Registro de una prueba de look. NO guarda imágenes: solo qué se pidió y cómo respondió el sistema."""
    consulta_id: uuid.UUID
    origen: OrigenSolicitud
    tipo_corte: TipoCorte
    fuente_prompt: str
    modo: str
    latencia_ms: int
    estilo_id: uuid.UUID | None = None
    instruccion: str | None = None
    elegida_en: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creada_en: datetime = field(default_factory=ahora)


@dataclass
class Consulta:
    estilista_id: uuid.UUID
    consentimiento_version: str
    consentimiento_otorgado_en: datetime
    estado: EstadoConsulta = EstadoConsulta.ACTIVA
    iniciada_en: datetime = field(default_factory=ahora)
    finalizada_en: datetime | None = None
    datos_eliminados_en: datetime | None = None
    satisfaccion: int | None = None
    simulaciones: list[Simulacion] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @classmethod
    def iniciar(cls, estilista_id: uuid.UUID, acepta_consentimiento: bool, version: str) -> "Consulta":
        if not acepta_consentimiento:
            raise EntradaInvalida("Sin el consentimiento del cliente no se puede usar la cámara (Ley N.° 29733).")
        if version != VERSION_CONSENTIMIENTO:
            raise Conflicto("El texto de consentimiento cambió. Recarga la página y muéstralo de nuevo al cliente.")
        t = ahora()
        return cls(estilista_id=estilista_id, consentimiento_version=version, consentimiento_otorgado_en=t, iniciada_en=t)

    # --- invariantes ---
    def verificar_estilista(self, estilista_id: uuid.UUID) -> None:
        if self.estilista_id != estilista_id:
            raise Prohibido("Esta consulta pertenece a otro estilista.")

    def asegurar_activa(self) -> None:
        if self.estado != EstadoConsulta.ACTIVA:
            raise Conflicto("La consulta ya terminó y sus datos fueron eliminados. Inicia una nueva.")

    # --- comportamiento ---
    def registrar_simulacion(self, **datos) -> Simulacion:
        self.asegurar_activa()
        if len(self.simulaciones) >= MAX_SIMULACIONES:
            raise Conflicto(f"Se alcanzó el límite de {MAX_SIMULACIONES} simulaciones en esta consulta.")
        sim = Simulacion(consulta_id=self.id, **datos)
        self.simulaciones.append(sim)
        return sim

    def elegir_look(self, simulacion_id: uuid.UUID) -> Simulacion:
        """El cliente decide: marca el fin del 'tiempo de indecisión' (KPI del OE4)."""
        self.asegurar_activa()
        elegida = next((s for s in self.simulaciones if s.id == simulacion_id), None)
        if not elegida:
            raise NoEncontrado("Ese look no pertenece a esta consulta.")
        t = ahora()
        for s in self.simulaciones:
            s.elegida_en = t if s is elegida else None
        return elegida

    def finalizar(self, satisfaccion: int | None) -> None:
        self.asegurar_activa()
        if satisfaccion is not None and not 1 <= satisfaccion <= 10:
            raise EntradaInvalida("La satisfacción va de 1 a 10.")
        self._cerrar(EstadoConsulta.FINALIZADA)
        self.satisfaccion = satisfaccion

    def revocar_consentimiento(self) -> None:
        self.asegurar_activa()
        self._cerrar(EstadoConsulta.CANCELADA)

    def expirar(self) -> None:
        if self.estado == EstadoConsulta.ACTIVA:
            self._cerrar(EstadoConsulta.EXPIRADA)

    def _cerrar(self, estado: EstadoConsulta) -> None:
        t = ahora()
        self.estado, self.finalizada_en, self.datos_eliminados_en = estado, t, t

    @property
    def look_elegido(self) -> Simulacion | None:
        return next((s for s in self.simulaciones if s.elegida_en), None)
