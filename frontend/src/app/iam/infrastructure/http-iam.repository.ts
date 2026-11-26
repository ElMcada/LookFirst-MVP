import { inject, Injectable } from '@angular/core';
import { Api } from '@core/http/api';
import { IamRepository } from '@iam/application/iam.repository';
import { NuevoUsuario, Sesion, Usuario } from '@iam/domain/usuario';

@Injectable()
export class HttpIamRepository extends IamRepository {
  private readonly api = inject(Api);

  login(email: string, password: string) { return this.api.post<Sesion>('/auth/login', { email, password }); }
  yo() { return this.api.get<Usuario>('/auth/me'); }
  listar() { return this.api.get<Usuario[]>('/usuarios'); }
  registrar(datos: NuevoUsuario) { return this.api.post<Usuario>('/usuarios', datos); }
  cambiarEstado(id: string, activo: boolean) { return this.api.patch<Usuario>(`/usuarios/${id}`, { activo }); }
}
