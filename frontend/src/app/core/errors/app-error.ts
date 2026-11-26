import { HttpErrorResponse } from '@angular/common/http';

/** Error con un mensaje listo para mostrar al usuario. */
export class AppError extends Error {
  constructor(message: string, readonly status = 0) {
    super(message);
  }
}

export function desdeHttp(e: HttpErrorResponse): AppError {
  if (e.status === 0) return new AppError('No hay conexión con el servidor. ¿Está corriendo en el puerto 8000?', 0);
  const detail = e.error?.detail;
  if (typeof detail === 'string') return new AppError(detail, e.status);
  if (Array.isArray(detail)) return new AppError(detail.map((d: { msg: string }) => d.msg).join(' · '), e.status);
  return new AppError(e.status >= 500 ? 'Error interno del servidor.' : 'La solicitud no es válida.', e.status);
}

export function mensajeDe(e: unknown): string {
  return e instanceof Error ? e.message : 'Ocurrió un error inesperado.';
}
