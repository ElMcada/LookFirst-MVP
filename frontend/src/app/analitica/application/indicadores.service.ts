import { inject, Injectable } from '@angular/core';
import { aBarras, aKpis, Barra, Kpi, Metricas } from '@analitica/domain/indicadores';

export interface FiltroMetricas { desde: string; hasta: string; estilistaId: string | null; }

/** Puerto de lectura de métricas. */
export abstract class MetricasRepository {
  abstract resumen(f: FiltroMetricas): Promise<Metricas>;
}

export interface Indicadores {
  kpis: Kpi[];
  origenes: Barra[];
  modos: Barra[];
  topLooks: { nombre: string; veces: number }[];
  promedioLooks: number | null;
  simulaciones: number;
}

@Injectable({ providedIn: 'root' })
export class IndicadoresService {
  private readonly repo = inject(MetricasRepository);

  async obtener(f: FiltroMetricas): Promise<Indicadores> {
    const m = await this.repo.resumen(f);
    return {
      kpis: aKpis(m),
      origenes: aBarras(m.simulaciones.por_origen),
      modos: aBarras(m.simulaciones.por_modo),
      topLooks: m.looks_mas_elegidos,
      promedioLooks: m.simulaciones.promedio_por_consulta,
      simulaciones: m.latencia.simulaciones,
    };
  }
}
