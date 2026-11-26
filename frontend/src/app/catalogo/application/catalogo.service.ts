import { inject, Injectable } from '@angular/core';
import { AppError } from '@core/errors/app-error';
import { DatosEstilo, Estilo, normalizar, validar } from '@catalogo/domain/estilo';

/** Puerto del catálogo. */
export abstract class CatalogoRepository {
  abstract listar(incluirInactivos: boolean): Promise<Estilo[]>;
  abstract crear(datos: DatosEstilo): Promise<Estilo>;
  abstract actualizar(id: string, datos: DatosEstilo): Promise<Estilo>;
  abstract cambiarEstado(id: string, activo: boolean): Promise<Estilo>;
}

@Injectable({ providedIn: 'root' })
export class CatalogoService {
  private readonly repo = inject(CatalogoRepository);

  listar(incluirInactivos = false): Promise<Estilo[]> {
    return this.repo.listar(incluirInactivos);
  }

  guardar(datos: DatosEstilo, id: string | null): Promise<Estilo> {
    const estilo = normalizar(datos);
    const errores = validar(estilo);
    if (errores.length) throw new AppError(errores.join(' '));
    return id ? this.repo.actualizar(id, estilo) : this.repo.crear(estilo);
  }

  cambiarEstado(e: Estilo, activo: boolean): Promise<Estilo> {
    return this.repo.cambiarEstado(e.id, activo);
  }
}
