import { inject, Injectable } from '@angular/core';
import { Api } from '@core/http/api';
import { CatalogoRepository } from '@catalogo/application/catalogo.service';
import { DatosEstilo, Estilo } from '@catalogo/domain/estilo';

@Injectable()
export class HttpCatalogoRepository extends CatalogoRepository {
  private readonly api = inject(Api);

  listar(todos: boolean) { return this.api.get<Estilo[]>('/estilos', todos ? { todos: 'true' } : undefined); }
  crear(datos: DatosEstilo) { return this.api.post<Estilo>('/estilos', datos); }
  actualizar(id: string, datos: DatosEstilo) { return this.api.put<Estilo>(`/estilos/${id}`, datos); }
  cambiarEstado(id: string, activo: boolean) { return this.api.patch<Estilo>(`/estilos/${id}`, { activo }); }
}
