import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { SesionStore } from '@iam/application/sesion.store';

/** Añade el token a cada petición y, si el servidor lo rechaza, vuelve al login. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const sesion = inject(SesionStore);
  const router = inject(Router);
  const token = sesion.token();
  const conToken = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
  return next(conToken).pipe(
    catchError((e: unknown) => {
      if (e instanceof HttpErrorResponse && e.status === 401 && token) {
        sesion.cerrar();
        router.navigate(['/login'], { queryParams: { expirada: 1 } });
      }
      return throwError(() => e);
    }),
  );
};
