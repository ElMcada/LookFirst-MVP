import { aBarras, aKpis, Metricas } from '@analitica/domain/indicadores';
import { estiloVacio, normalizar, validar } from '@catalogo/domain/estilo';
import { aLook, cumpleLatencia, pasoActual } from '@consulta/domain/consulta';
import { iniciales, validarNuevoUsuario } from '@iam/domain/usuario';

describe('Catálogo · reglas de estilo', () => {
  it('un tinte siempre conserva la silueta y normaliza el color', () => {
    const e = normalizar({ ...estiloVacio(), tipo: 'tinte', tipo_corte: 'corto', color_hex: '#aabbcc', degradado: true });
    expect(e.tipo_corte).toBe('conservar');
    expect(e.color_hex).toBe('#AABBCC');
  });
  it('un corte no puede quedar en "conservar" ni con degradado', () => {
    const e = normalizar({ ...estiloVacio(), tipo: 'corte', tipo_corte: 'conservar', degradado: true });
    expect(e.tipo_corte).toBe('medio');
    expect(e.degradado).toBe(false);
  });
  it('valida código, prompt, formas y color de tinte', () => {
    const errores = validar(normalizar({ ...estiloVacio(), codigo: 'Mal Código', tipo: 'tinte' }));
    expect(errores.length).toBe(5);
  });
});

describe('Consulta · reglas', () => {
  it('calcula el paso actual', () => {
    expect(pasoActual({ activa: false, conFoto: false, elegido: false })).toBe('consentimiento');
    expect(pasoActual({ activa: true, conFoto: true, elegido: false })).toBe('explorar');
  });
  it('mide la latencia contra el límite de 6 s (REQ-04)', () => {
    const base = { id: 'a', etiqueta: 'x', imagen_b64: 'AA', modo: 'ia_generativa' as const, tipo_corte: 'medio' as const, fuente_prompt: 'llm', prompt_en: '', aviso: null };
    expect(cumpleLatencia(aLook({ ...base, latencia_s: 5.9 }, 'texto'))).toBe(true);
    expect(cumpleLatencia(aLook({ ...base, latencia_s: 6.1 }, 'texto'))).toBe(false);
  });
});

describe('IAM', () => {
  it('iniciales y validación de cuentas', () => {
    expect(iniciales('ana maría quispe')).toBe('AM');
    expect(validarNuevoUsuario({ nombre: 'A', email: 'x', password: '123', rol: 'estilista' }).length).toBe(3);
  });
});

describe('Analítica · indicadores', () => {
  const m: Metricas = {
    desde: '', hasta: '',
    consultas: { total: 4, activas: 0, finalizadas: 3, canceladas: 1, expiradas: 0 },
    decision: { consultas_con_decision: 3, tasa_decision: 0.75, tiempo_promedio_min: 3, duracion_promedio_consulta_min: 8, tiempo_tradicional_min: 10, reduccion: 0.7, cumple_kpi: true },
    satisfaccion: { respuestas: 3, promedio: 8.7, cumple_kpi: true },
    latencia: { simulaciones: 10, promedio_s: 4.2, p95_s: 5.8, dentro_limite: 0.9, limite_s: 6, cumple_kpi: true },
    simulaciones: { promedio_por_consulta: 2.5, por_origen: { voz: 1, texto: 3 }, por_modo: {} },
    looks_mas_elegidos: [],
  };
  it('traduce las métricas a los 4 KPIs del charter', () => {
    const k = aKpis(m);
    expect(k.map((x) => x.titulo)).toEqual(['Tiempo hasta decidir', 'Satisfacción', 'Latencia promedio', 'Consultas']);
    expect(k[0].detalle).toContain('70 %');
  });
  it('ordena las barras de mayor a menor', () => {
    expect(aBarras(m.simulaciones.por_origen)).toEqual([
      { etiqueta: 'Texto', valor: 3, porcentaje: 75 }, { etiqueta: 'Voz', valor: 1, porcentaje: 25 },
    ]);
  });
});
