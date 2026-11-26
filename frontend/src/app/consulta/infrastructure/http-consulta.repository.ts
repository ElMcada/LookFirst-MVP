import { inject, Injectable } from '@angular/core';
import { Api } from '@core/http/api';
import { SesionStore } from '@iam/application/sesion.store';
import { ConsultaRepository, PedidoSimulacion } from '@consulta/application/puertos';
import { AnalisisRostro, SimulacionDto } from '@consulta/domain/consulta';

@Injectable()
export class HttpConsultaRepository extends ConsultaRepository {
  private readonly api = inject(Api);
  private readonly sesion = inject(SesionStore);

  iniciar(version: string) {
    return this.api.post<{ id: string }>('/consultas', { acepta_consentimiento: true, version_consentimiento: version });
  }

  subirFoto(id: string, foto: Blob) {
    const fd = new FormData();
    fd.append('file', foto, 'captura.jpg');
    return this.api.post<AnalisisRostro>(`/consultas/${id}/foto`, fd);
  }

  simular(id: string, pedido: PedidoSimulacion) {
    return this.api.post<SimulacionDto>(`/consultas/${id}/simulaciones`, pedido);
  }

  async elegir(id: string, simulacionId: string) {
    await this.api.post(`/consultas/${id}/simulaciones/${simulacionId}/elegir`);
  }

  async finalizar(id: string, satisfaccion: number | null) {
    await this.api.post(`/consultas/${id}/finalizar`, { satisfaccion });
  }

  async revocar(id: string) {
    await this.api.post(`/consultas/${id}/revocar`);
  }

  finalizarAlSalir(id: string) {
    // fetch con keepalive: el navegador completa la petición aunque la pestaña se cierre
    fetch(this.api.url(`/consultas/${id}/finalizar`), {
      method: 'POST', keepalive: true,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${this.sesion.token()}` },
      body: JSON.stringify({ satisfaccion: null }),
    }).catch(() => {});
  }
}
