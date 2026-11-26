import uuid
from datetime import timedelta

import numpy as np
import pytest

from app.analitica.domain.metricas import FilaConsulta, FilaSimulacion, calcular
from app.catalogo.domain.estilo import Estilo, TipoServicio
from app.catalogo.domain.recomendacion import recomendar
from app.consulta.domain.consulta import MAX_SIMULACIONES, VERSION_CONSENTIMIENTO, Consulta, EstadoConsulta, OrigenSolicitud
from app.iam.infrastructure.seguridad import HasherScrypt
from app.shared.errores import Conflicto, EntradaInvalida, NoEncontrado
from app.shared.kernel import FormaRostro, TipoCorte, ahora
from app.simulacion.domain import imagen
from app.simulacion.domain.prompts import negative_prompt
from app.simulacion.domain.visagismo import clasificar_forma
from app.simulacion.infrastructure.interprete_palabras_clave import InterpretePalabrasClave

kw = InterpretePalabrasClave()


# ---------- Simulación ----------
@pytest.mark.parametrize("texto, tipo, color", [
    ("quiero rubio ceniza", TipoCorte.CONSERVAR, "#BDB2A0"),        # antes se clasificaba como 'short'
    ("pelo morado", TipoCorte.CONSERVAR, "#5A2D82"),
    ("un bob rubio", TipoCorte.MEDIO, "#D4B06A"),
    ("degradado a los lados", TipoCorte.CORTO, None),               # fade
    ("quiero calvo", TipoCorte.CALVO, None),
    ("largo con ondas", TipoCorte.LARGO, None),
])
def test_palabras_clave_tipo_de_cambio(texto, tipo, color):
    e = kw.interpretar(texto)
    assert e.tipo_corte == tipo and e.color_hex == color


def test_degradado_con_color_es_ombre_no_fade():
    e = kw.interpretar("degradado cobrizo")
    assert e.tipo_corte == TipoCorte.CONSERVAR and e.degradado


def test_pedido_sin_estilo_reconocible():
    assert kw.interpretar("hola qué tal") is None


def test_negative_prompt_calvo_solo_para_calvo():
    assert "hair on scalp" in negative_prompt(TipoCorte.CALVO)
    assert "hair on scalp" not in negative_prompt(TipoCorte.LARGO)
    assert "bald" in negative_prompt(TipoCorte.CONSERVAR)


def test_clasificar_forma():
    assert clasificar_forma(1.45, 0.8) == FormaRostro.ALARGADO
    assert clasificar_forma(1.2, 0.7) == FormaRostro.REDONDO
    assert clasificar_forma(1.2, 0.9) == FormaRostro.CUADRADO
    assert clasificar_forma(1.3, 0.8) == FormaRostro.OVALADO


def test_mascara_tinte_no_crece_y_protege_facciones():
    mask = np.zeros((200, 200), np.uint8); mask[20:80, 50:150] = 255
    escudo = np.zeros_like(mask); escudo[70:150, 70:130] = 255
    zona = imagen.mascara_trabajo(mask, escudo, TipoCorte.CONSERVAR)
    assert not (zona & escudo).any()
    assert (zona > 0).sum() < (imagen.mascara_trabajo(mask, escudo, TipoCorte.LARGO) > 0).sum()


def test_recorte_y_tamano_modelo():
    zona = np.zeros((600, 400), np.uint8); zona[100:300, 120:280] = 255
    x0, y0, x1, y1 = imagen.caja_recorte(zona)
    assert 0 <= x0 < x1 <= 400 and 0 <= y0 < y1 <= 600
    out = imagen.a_tamano_modelo(np.zeros((y1 - y0, x1 - x0, 3), np.uint8))
    assert out.shape[0] % 8 == 0 and out.shape[1] % 8 == 0 and max(out.shape[:2]) <= 512


# ---------- Catálogo ----------
def _estilo(codigo, tipo, formas, **kw):
    base = dict(nombre=codigo.title(), descripcion="", prompt_en="some long technical prompt",
                tipo_corte=TipoCorte.CONSERVAR if tipo == TipoServicio.TINTE else TipoCorte.MEDIO,
                color_hex="#112233" if tipo == TipoServicio.TINTE else None)
    base.update(kw)
    return Estilo(codigo=codigo, tipo=tipo, formas=formas, **base)


def test_tinte_debe_conservar_silueta_y_tener_color():
    with pytest.raises(EntradaInvalida):
        _estilo("x", TipoServicio.TINTE, {FormaRostro.OVALADO}, tipo_corte=TipoCorte.CORTO)
    with pytest.raises(EntradaInvalida):
        _estilo("x", TipoServicio.TINTE, {FormaRostro.OVALADO}, color_hex=None)
    with pytest.raises(EntradaInvalida):
        _estilo("x", TipoServicio.CORTE, {FormaRostro.OVALADO}, tipo_corte=TipoCorte.CONSERVAR)


def test_recomendar_solo_compatibles_y_mezcla_tipos():
    est = [_estilo("c1", TipoServicio.CORTE, {FormaRostro.REDONDO}), _estilo("c2", TipoServicio.CORTE, {FormaRostro.REDONDO}),
           _estilo("t1", TipoServicio.TINTE, {FormaRostro.REDONDO}), _estilo("c3", TipoServicio.CORTE, {FormaRostro.ALARGADO}),
           _estilo("c4", TipoServicio.CORTE, {FormaRostro.REDONDO}, activo=False)]
    r = recomendar(est, FormaRostro.REDONDO)
    assert [e.codigo for e in r] == ["c1", "t1", "c2"]


# ---------- Consulta ----------
def _consulta():
    return Consulta.iniciar(uuid.uuid4(), True, VERSION_CONSENTIMIENTO)


def _sim(c):
    return c.registrar_simulacion(origen=OrigenSolicitud.TEXTO, instruccion="rubio", tipo_corte=TipoCorte.CONSERVAR,
                                  fuente_prompt="palabras_clave", modo="respaldo_local", latencia_ms=100)


def test_sin_consentimiento_no_hay_consulta():
    with pytest.raises(EntradaInvalida):
        Consulta.iniciar(uuid.uuid4(), False, VERSION_CONSENTIMIENTO)
    with pytest.raises(Conflicto):
        Consulta.iniciar(uuid.uuid4(), True, "version-vieja")


def test_solo_un_look_elegido():
    c = _consulta(); a, b = _sim(c), _sim(c)
    c.elegir_look(a.id); c.elegir_look(b.id)
    assert c.look_elegido is b and a.elegida_en is None
    with pytest.raises(NoEncontrado):
        c.elegir_look(uuid.uuid4())


def test_cierre_deja_constancia_de_borrado_y_bloquea_cambios():
    c = _consulta(); c.finalizar(9)
    assert c.estado == EstadoConsulta.FINALIZADA and c.datos_eliminados_en is not None
    with pytest.raises(Conflicto):
        _sim(c)


def test_satisfaccion_fuera_de_rango():
    with pytest.raises(EntradaInvalida):
        _consulta().finalizar(11)


def test_cuota_de_simulaciones():
    c = _consulta()
    for _ in range(MAX_SIMULACIONES):
        _sim(c)
    with pytest.raises(Conflicto):
        _sim(c)


# ---------- IAM ----------
def test_hash_de_contrasena():
    h = HasherScrypt()
    hashed = h.hashear("secreta123")
    assert "secreta123" not in hashed and h.verificar("secreta123", hashed) and not h.verificar("otra", hashed)


# ---------- Analítica ----------
def test_metricas_kpis():
    t0 = ahora()
    cs = [FilaConsulta(1, "finalizada", t0, t0 + timedelta(minutes=10), 9),
          FilaConsulta(2, "finalizada", t0, t0 + timedelta(minutes=6), 8)]
    ss = [FilaSimulacion(1, "voz", "ia_generativa", 4000, None, "rubio", t0 + timedelta(minutes=4)),
          FilaSimulacion(1, "texto", "ia_generativa", 7000, None, "bob", None),
          FilaSimulacion(2, "catalogo", "respaldo_local", 500, "Bob en capas", None, t0 + timedelta(minutes=2))]
    m = calcular(cs, ss, tradicional_min=10)
    assert m["decision"]["tiempo_promedio_min"] == 3.0
    assert m["decision"]["reduccion"] == 0.7 and m["decision"]["cumple_kpi"]
    assert m["satisfaccion"]["promedio"] == 8.5 and m["satisfaccion"]["cumple_kpi"]
    assert m["latencia"]["dentro_limite"] == round(2 / 3, 3)
