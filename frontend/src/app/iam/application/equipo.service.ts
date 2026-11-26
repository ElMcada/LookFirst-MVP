import { inject, Injectable } from '@angular/core';
import { AppError } from '@core/errors/app-error';
import { NuevoUsuario, Usuario, validarNuevoUsuario } from '@iam/domain/usuario';
import { IamRepository } from './iam.repository';

/** Gestión del personal del salón (solo administrador). */
@Injectable({ providedIn: 'root' })
export class EquipoService {
  private readonly repo = inject(IamRepository);

  listar(): Promise<Usuario[]> {
    return this.repo.listar();
  }

  registrar(datos: NuevoUsuario): Promise<Usuario> {
    const errores = validarNuevoUsuario(datos);
    if (errores.length) throw new AppError(errores.join(' '));
    return this.repo.registrar({ ...datos, nombre: datos.nombre.trim(), email: datos.email.trim().toLowerCase() });
  }

  cambiarEstado(u: Usuario, activo: boolean): Promise<Usuario> {
    return this.repo.cambiarEstado(u.id, activo);
  }
}
