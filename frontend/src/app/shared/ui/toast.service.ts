import { Injectable, signal } from '@angular/core';

export type TipoToast = 'ok' | 'error' | 'info';
export interface Toast { id: number; tipo: TipoToast; texto: string; }

@Injectable({ providedIn: 'root' })
export class ToastService {
  private siguiente = 1;
  readonly toasts = signal<Toast[]>([]);

  ok(texto: string) { this.mostrar('ok', texto); }
  error(texto: string) { this.mostrar('error', texto, 6000); }
  info(texto: string) { this.mostrar('info', texto); }

  cerrar(id: number) { this.toasts.update((t) => t.filter((x) => x.id !== id)); }

  private mostrar(tipo: TipoToast, texto: string, ms = 4000) {
    const id = this.siguiente++;
    this.toasts.update((t) => [...t.slice(-2), { id, tipo, texto }]);
    setTimeout(() => this.cerrar(id), ms);
  }
}
