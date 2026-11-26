"""Caso de uso del BC Simulación: preparar la foto y generar un look dentro del presupuesto de latencia."""
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from app.shared.errores import EntradaInvalida
from app.shared.kernel import TipoCorte
from app.simulacion.domain import imagen
from app.simulacion.domain.modelos import EspecificacionLook, FotoPreparada, FuentePrompt, ModoSimulacion, ResultadoLook
from app.simulacion.domain.prompts import negative_prompt, prompt_final
from app.simulacion.domain.puertos import AnalizadorFacial, Inpainter, InterpreteInstrucciones, SegmentadorCabello

RESERVA_S = 0.4          # mezcla + codificación JPEG
MIN_INPAINT_S = 1.5      # por debajo no vale la pena llamar a la GPU
AVISO_SOLO_COLOR = "Sin conexión con la IA generativa: solo se simuló el color. El cambio de corte requiere Colab activo."
AVISO_SIN_CAMBIO = "Sin conexión con la IA generativa: el modo de respaldo solo cambia el color y este pedido no tiene color."


class MotorSimulacion:
    def __init__(self, analizador: AnalizadorFacial, segmentador: SegmentadorCabello, inpainter: Inpainter,
                 interprete_respaldo: InterpreteInstrucciones, interprete_ia: InterpreteInstrucciones | None = None,
                 llm_timeout_s: float = 2.5, max_lado: int = 896):
        self.analizador, self.segmentador, self.inpainter = analizador, segmentador, inpainter
        self.interprete_ia, self.interprete_respaldo = interprete_ia, interprete_respaldo
        self.llm_timeout_s, self.max_lado = llm_timeout_s, max_lado
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm")

    def preparar_foto(self, raw: bytes) -> FotoPreparada:
        """Análisis facial + segmentación se hacen UNA vez por foto, no en cada simulación."""
        bgr = imagen.decodificar(raw, self.max_lado)
        analisis, escudo = self.analizador.analizar(bgr)
        mascara, matte = self.segmentador.segmentar(bgr)
        return FotoPreparada(bgr=bgr, mascara=mascara, matte=matte, escudo=escudo, analisis=analisis)

    def interpretar(self, texto: str) -> EspecificacionLook:
        texto = (texto or "").strip()
        if not texto:
            raise EntradaInvalida("Escribe o di qué estilo quieres.")
        if len(texto) > 300:
            raise EntradaInvalida("La instrucción es demasiado larga (máx. 300 caracteres).")
        if self.interprete_ia:
            try:
                espec = self._pool.submit(self.interprete_ia.interpretar, texto).result(timeout=self.llm_timeout_s)
                if espec:
                    return espec
            except FutureTimeout:
                print("[LLM] tardó más de", self.llm_timeout_s, "s; uso palabras clave")
            except Exception as e:  # la red o el proveedor fallan: nunca debe tumbar la consulta
                print("[LLM] error, uso palabras clave:", type(e).__name__, e)
        espec = self.interprete_respaldo.interpretar(texto)
        if not espec:
            raise EntradaInvalida("No entendí el estilo. Menciona un corte (bob, pixie, largo…) o un color (rubio, cobrizo…).")
        return espec

    @staticmethod
    def especificacion_catalogo(prompt_en: str, tipo_corte: TipoCorte, color_hex: str | None,
                                degradado: bool) -> EspecificacionLook:
        return EspecificacionLook(prompt_en=prompt_en, tipo_corte=tipo_corte, fuente=FuentePrompt.CATALOGO,
                                  color_hex=color_hex, degradado=degradado)

    def generar(self, foto: FotoPreparada, espec: EspecificacionLook, presupuesto_s: float,
                inicio: float | None = None) -> ResultadoLook:
        inicio = inicio if inicio is not None else time.perf_counter()
        zona = imagen.mascara_trabajo(foto.mascara, foto.escudo, espec.tipo_corte)
        restante = presupuesto_s - (time.perf_counter() - inicio) - RESERVA_S

        if self.inpainter.disponible and restante >= MIN_INPAINT_S:
            x0, y0, x1, y1 = imagen.caja_recorte(zona)
            recorte, zona_rec = foto.bgr[y0:y1, x0:x1], zona[y0:y1, x0:x1]
            gen = self.inpainter.generar(imagen.a_tamano_modelo(recorte), imagen.a_tamano_modelo(zona_rec, True),
                                         prompt_final(espec), negative_prompt(espec.tipo_corte), restante)
            if gen is not None:
                completo = imagen.pegar(foto.bgr, gen, (x0, y0, x1, y1))
                alpha = foto.matte if espec.tipo_corte == TipoCorte.CONSERVAR else imagen.suavizar(zona)
                out = imagen.mezclar(foto.bgr, completo, alpha)
                return ResultadoLook(imagen.codificar_jpg(out), ModoSimulacion.IA_GENERATIVA, None)

        if espec.color_hex:
            out = imagen.mezclar(foto.bgr, imagen.recolorear(foto.bgr, foto.mascara, espec.color_hex, espec.degradado), foto.matte)
            aviso = None if espec.tipo_corte == TipoCorte.CONSERVAR else AVISO_SOLO_COLOR
        else:
            out, aviso = foto.bgr, AVISO_SIN_CAMBIO
        return ResultadoLook(imagen.codificar_jpg(out), ModoSimulacion.RESPALDO_LOCAL, aviso)
