import { ElementRef, Signal } from '@angular/core';

/** Base para diálogos modales nativos (<dialog>): abrir() devuelve una promesa con la respuesta. */
export abstract class Dialogo<T> {
  protected abstract readonly ref: Signal<ElementRef<HTMLDialogElement>>;
  private resolver: ((v: T) => void) | null = null;

  protected abrirCon(valorAlCancelar: T): Promise<T> {
    const d = this.ref().nativeElement;
    d.oncancel = (e) => { e.preventDefault(); this.responder(valorAlCancelar); }; // tecla Esc
    d.showModal();
    return new Promise<T>((ok) => (this.resolver = ok));
  }

  protected responder(valor: T): void {
    this.ref().nativeElement.close();
    this.resolver?.(valor);
    this.resolver = null;
  }
}
