import { Injectable } from '@angular/core';
import { AlmacenSesion } from '@iam/application/iam.repository';
import { Sesion } from '@iam/domain/usuario';

const CLAVE = 'lookfirst.sesion';

/** sessionStorage: la sesión se cierra sola al cerrar el navegador del salón. */
@Injectable()
export class SessionStorageAlmacen extends AlmacenSesion {
  leer(): Sesion | null {
    try {
      const raw = sessionStorage.getItem(CLAVE);
      const s = raw ? (JSON.parse(raw) as Sesion) : null;
      return s?.token && s.usuario ? s : null;
    } catch {
      return null;
    }
  }
  guardar(s: Sesion) { sessionStorage.setItem(CLAVE, JSON.stringify(s)); }
  borrar() { sessionStorage.removeItem(CLAVE); }
}
