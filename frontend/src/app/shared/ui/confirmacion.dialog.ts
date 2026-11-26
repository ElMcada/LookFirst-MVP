import { ChangeDetectionStrategy, Component, ElementRef, signal, viewChild } from '@angular/core';
import { Dialogo } from './dialogo';

export interface OpcionesConfirmacion { titulo: string; texto: string; confirmar: string; peligro?: boolean; }

@Component({
  selector: 'lf-confirmacion',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <dialog #d class="modal" aria-labelledby="conf-titulo">
      <div class="modal-body">
        <h2 id="conf-titulo">{{ op().titulo }}</h2>
        <p class="muted">{{ op().texto }}</p>
      </div>
      <div class="modal-foot">
        <button class="btn btn-secondary" (click)="responder(false)">Cancelar</button>
        <button class="btn" [class.btn-primary]="!op().peligro" [class.peligro]="op().peligro" (click)="responder(true)">{{ op().confirmar }}</button>
      </div>
    </dialog>
  `,
  styles: `.peligro { background: var(--danger); color: #fff; } .peligro:hover { background: #912018; }`,
})
export class ConfirmacionDialog extends Dialogo<boolean> {
  protected readonly ref = viewChild.required<ElementRef<HTMLDialogElement>>('d');
  protected readonly op = signal<OpcionesConfirmacion>({ titulo: '', texto: '', confirmar: 'Aceptar' });

  pedir(op: OpcionesConfirmacion): Promise<boolean> {
    this.op.set(op);
    return this.abrirCon(false);
  }
  protected override responder(v: boolean) { super.responder(v); }
}
