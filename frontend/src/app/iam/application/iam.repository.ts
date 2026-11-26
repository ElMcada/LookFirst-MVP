import { NuevoUsuario, Sesion, Usuario } from '@iam/domain/usuario';

/** Puerto: lo que IAM necesita del exterior. La implementación HTTP vive en infrastructure/. */
export abstract class IamRepository {
  abstract login(email: string, password: string): Promise<Sesion>;
  abstract yo(): Promise<Usuario>;
  abstract listar(): Promise<Usuario[]>;
  abstract registrar(datos: NuevoUsuario): Promise<Usuario>;
  abstract cambiarEstado(id: string, activo: boolean): Promise<Usuario>;
}

/** Puerto: dónde se guarda la sesión del navegador. */
export abstract class AlmacenSesion {
  abstract leer(): Sesion | null;
  abstract guardar(s: Sesion): void;
  abstract borrar(): void;
}
