import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SesionStore } from '@iam/application/sesion.store';

// inject() solo funciona antes del primer await: se resuelven las dependencias al inicio.

export const autenticadoGuard: CanActivateFn = async () => {
  const sesion = inject(SesionStore);
  const router = inject(Router);
  return (await sesion.verificar()) || router.createUrlTree(['/login']);
};

export const adminGuard: CanActivateFn = () => {
  return inject(SesionStore).esAdmin() || inject(Router).createUrlTree(['/consulta']);
};

export const invitadoGuard: CanActivateFn = () => {
  return !inject(SesionStore).autenticado() || inject(Router).createUrlTree(['/consulta']);
};
