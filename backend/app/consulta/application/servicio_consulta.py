"""Casos de uso de la consulta. Orquesta Catálogo (qué ofrece el salón) y Simulación (motor de IA)."""
import time
import uuid
from dataclasses import dataclass

from app.consulta.domain.consulta import Consulta, OrigenSolicitud, Simulacion
from app.consulta.domain.puertos import AlmacenFotosTemporal, ProveedorEstilos, RepositorioConsultas
from app.shared.errores import EntradaInvalida, NoEncontrado
from app.simulacion.application.motor import MotorSimulacion
from app.simulacion.domain.modelos import ResultadoLook


@dataclass(frozen=True)
class ResultadoSimulacion:
    simulacion: Simulacion
    look: ResultadoLook
    prompt_en: str
    etiqueta: str


class ServicioConsulta:
    def __init__(self, repo: RepositorioConsultas, fotos: AlmacenFotosTemporal, estilos: ProveedorEstilos,
                 motor: MotorSimulacion, presupuesto_s: float):
        self.repo, self.fotos, self.estilos, self.motor, self.presupuesto_s = repo, fotos, estilos, motor, presupuesto_s

    def _consulta_activa(self, estilista_id: uuid.UUID, consulta_id: uuid.UUID) -> Consulta:
        c = self.repo.por_id(consulta_id)
        if not c:
            raise NoEncontrado("Consulta no encontrada.")
        c.verificar_estilista(estilista_id)
        c.asegurar_activa()
        return c

    def iniciar(self, estilista_id: uuid.UUID, acepta: bool, version: str) -> Consulta:
        c = Consulta.iniciar(estilista_id, acepta, version)
        self.repo.guardar(c)
        return c

    def analizar_foto(self, estilista_id: uuid.UUID, consulta_id: uuid.UUID, raw: bytes) -> dict:
        self._consulta_activa(estilista_id, consulta_id)
        foto = self.motor.preparar_foto(raw)
        self.fotos.guardar(consulta_id, foto)   # reemplaza la foto anterior si se toma otra
        razon, recomendados = self.estilos.recomendar(foto.analisis.forma)
        return {"forma_rostro": foto.analisis.forma.value, "metricas": foto.analisis.metricas,
                "razon": razon, "recomendaciones": recomendados}

    def simular(self, estilista_id: uuid.UUID, consulta_id: uuid.UUID, origen: OrigenSolicitud,
                estilo_id: uuid.UUID | None = None, instruccion: str | None = None) -> ResultadoSimulacion:
        inicio = time.perf_counter()
        c = self._consulta_activa(estilista_id, consulta_id)
        foto = self.fotos.obtener(consulta_id)
        if foto is None:
            raise NoEncontrado("No hay foto en esta consulta (o venció). Captura o sube una foto de nuevo.")

        if origen == OrigenSolicitud.CATALOGO:
            if not estilo_id:
                raise EntradaInvalida("Indica el estilo del catálogo.")
            e = self.estilos.obtener(estilo_id)
            espec = self.motor.especificacion_catalogo(e.prompt_en, e.tipo_corte, e.color_hex, e.degradado)
            etiqueta, instruccion = e.nombre, None
        else:
            espec = self.motor.interpretar(instruccion or "")
            etiqueta, estilo_id, instruccion = (instruccion or "").strip(), None, (instruccion or "").strip()

        look = self.motor.generar(foto, espec, self.presupuesto_s, inicio)
        latencia_ms = int((time.perf_counter() - inicio) * 1000)
        sim = c.registrar_simulacion(origen=origen, estilo_id=estilo_id, instruccion=instruccion,
                                     tipo_corte=espec.tipo_corte, fuente_prompt=espec.fuente.value,
                                     modo=look.modo.value, latencia_ms=latencia_ms)
        self.repo.guardar(c)
        return ResultadoSimulacion(simulacion=sim, look=look, prompt_en=espec.prompt_en, etiqueta=etiqueta)

    def elegir_look(self, estilista_id: uuid.UUID, consulta_id: uuid.UUID, simulacion_id: uuid.UUID) -> Simulacion:
        c = self._consulta_activa(estilista_id, consulta_id)
        sim = c.elegir_look(simulacion_id)
        self.repo.guardar(c)
        return sim

    def finalizar(self, estilista_id: uuid.UUID, consulta_id: uuid.UUID, satisfaccion: int | None) -> Consulta:
        c = self._consulta_activa(estilista_id, consulta_id)
        c.finalizar(satisfaccion)
        self.fotos.eliminar(consulta_id)
        self.repo.guardar(c)
        return c

    def revocar_consentimiento(self, estilista_id: uuid.UUID, consulta_id: uuid.UUID) -> Consulta:
        c = self._consulta_activa(estilista_id, consulta_id)
        c.revocar_consentimiento()
        self.fotos.eliminar(consulta_id)
        self.repo.guardar(c)
        return c

    def expirar_vencidas(self, ttl_s: float) -> int:
        """Política de borrado automático (REQ-09): fotos sin cerrar se eliminan al vencer el TTL."""
        n = 0
        for consulta_id in self.fotos.vencidas(ttl_s):
            self.fotos.eliminar(consulta_id)
            c = self.repo.por_id(consulta_id)
            if c:
                c.expirar()
                self.repo.guardar(c)
            n += 1
        return n

    def expirar_huerfanas(self) -> int:
        """Al arrancar el servidor la memoria está vacía: toda consulta 'activa' ya perdió su foto."""
        activas = self.repo.activas()
        for c in activas:
            if self.fotos.obtener(c.id) is None:
                c.expirar()
                self.repo.guardar(c)
        return len(activas)
