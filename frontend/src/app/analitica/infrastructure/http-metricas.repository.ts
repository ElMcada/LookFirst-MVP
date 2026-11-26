import { inject, Injectable } from '@angular/core';
import { Api } from '@core/http/api';
import { FiltroMetricas, MetricasRepository } from '@analitica/application/indicadores.service';
import { Metricas } from '@analitica/domain/indicadores';

@Injectable()
export class HttpMetricasRepository extends MetricasRepository {
  private readonly api = inject(Api);

  resumen(f: FiltroMetricas) {
    const params: Record<string, string> = { desde: f.desde, hasta: f.hasta };
    if (f.estilistaId) params['estilista_id'] = f.estilistaId;
    return this.api.get<Metricas>('/metricas', params);
  }
}
