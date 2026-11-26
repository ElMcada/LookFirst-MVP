import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom, Observable } from 'rxjs';
import { APP_CONFIG } from '@core/config/app-config';
import { desdeHttp } from '@core/errors/app-error';

/** Cliente HTTP base de los adaptadores de infraestructura: devuelve promesas y errores legibles. */
@Injectable({ providedIn: 'root' })
export class Api {
  private readonly http = inject(HttpClient);
  readonly baseUrl = inject(APP_CONFIG).apiUrl;

  get<T>(path: string, params?: Record<string, string>): Promise<T> {
    return this.run(this.http.get<T>(this.url(path), { params }));
  }
  post<T>(path: string, body: unknown = {}): Promise<T> {
    return this.run(this.http.post<T>(this.url(path), body));
  }
  put<T>(path: string, body: unknown): Promise<T> {
    return this.run(this.http.put<T>(this.url(path), body));
  }
  patch<T>(path: string, body: unknown): Promise<T> {
    return this.run(this.http.patch<T>(this.url(path), body));
  }

  url(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  private async run<T>(obs: Observable<T>): Promise<T> {
    try {
      return await firstValueFrom(obs);
    } catch (e) {
      throw e instanceof HttpErrorResponse ? desdeHttp(e) : e;
    }
  }
}
