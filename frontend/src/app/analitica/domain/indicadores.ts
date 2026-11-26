/** Respuesta de /metricas y su traducción a los indicadores del Project Charter (OE4, REQ-04). */
export interface Metricas {
  desde: string;
  hasta: string;
  consultas: { total: number; activas: number; finalizadas: number; canceladas: number; expiradas: number };
  decision: {
    consultas_con_decision: number; tasa_decision: number | null; tiempo_promedio_min: number | null;
    duracion_promedio_consulta_min: number | null; tiempo_tradicional_min: number | null;
    reduccion: number | null; cumple_kpi: boolean | null;
  };
  satisfaccion: { respuestas: number; promedio: number | null; cumple_kpi: boolean | null };
  latencia: { simulaciones: number; promedio_s: number | null; p95_s: number | null; dentro_limite: number | null; limite_s: number; cumple_kpi: boolean | null };
  simulaciones: { promedio_por_consulta: number | null; por_origen: Record<string, number>; por_modo: Record<string, number> };
  looks_mas_elegidos: { nombre: string; veces: number }[];
}

export interface Kpi {
  titulo: string;
  valor: string;
  unidad: string;
  meta: string;
  detalle: string;
  cumple: boolean | null;
}

export interface Barra { etiqueta: string; valor: number; porcentaje: number; }

const ETIQUETAS: Record<string, string> = {
  catalogo: 'Catálogo', texto: 'Texto', voz: 'Voz', ia_generativa: 'IA generativa', respaldo_local: 'Respaldo local',
};

const pct = (x: number | null) => (x == null ? '—' : `${Math.round(x * 100)} %`);
const num = (x: number | null, dec = 1) => (x == null ? '—' : x.toFixed(dec).replace(/\.0$/, ''));

export function aKpis(m: Metricas): Kpi[] {
  const d = m.decision;
  return [
    {
      titulo: 'Tiempo hasta decidir', valor: num(d.tiempo_promedio_min), unidad: 'min', meta: 'Meta −40 %', cumple: d.cumple_kpi,
      detalle: d.reduccion == null
        ? 'Configura el tiempo del método tradicional para medir la reducción.'
        : `${pct(d.reduccion)} menos que el método tradicional (${d.tiempo_tradicional_min} min).`,
    },
    {
      titulo: 'Satisfacción', valor: num(m.satisfaccion.promedio), unidad: '/ 10', meta: 'Meta > 8', cumple: m.satisfaccion.cumple_kpi,
      detalle: `${m.satisfaccion.respuestas} respuesta(s) de clientes.`,
    },
    {
      titulo: 'Latencia promedio', valor: num(m.latencia.promedio_s), unidad: 's', meta: `Meta ≤ ${m.latencia.limite_s} s`, cumple: m.latencia.cumple_kpi,
      detalle: `${pct(m.latencia.dentro_limite)} dentro del límite · p95 ${num(m.latencia.p95_s)} s.`,
    },
    {
      titulo: 'Consultas', valor: String(m.consultas.total), unidad: '', meta: `Decisión ${pct(d.tasa_decision)}`, cumple: null,
      detalle: `${m.consultas.finalizadas} finalizadas · ${m.consultas.canceladas} canceladas · ${m.consultas.expiradas} expiradas.`,
    },
  ];
}

export function aBarras(conteos: Record<string, number>): Barra[] {
  const total = Object.values(conteos).reduce((a, b) => a + b, 0);
  return Object.entries(conteos)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ etiqueta: ETIQUETAS[k] ?? k, valor: v, porcentaje: total ? Math.round((v / total) * 100) : 0 }));
}

export function rangoPorDefecto(hoy = new Date()): { desde: string; hasta: string } {
  const iso = (d: Date) => d.toLocaleDateString('en-CA'); // YYYY-MM-DD en hora local
  return { desde: iso(new Date(hoy.getTime() - 30 * 864e5)), hasta: iso(hoy) };
}
