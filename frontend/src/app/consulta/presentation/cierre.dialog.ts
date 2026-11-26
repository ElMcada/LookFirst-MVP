import { ChangeDetectionStrategy, Component, ElementRef, signal, viewChild } from '@angular/core';
import { Dialogo } from '@shared/ui/dialogo';
import { IconComponent } from '@shared/ui/icon.component';

export interface Cierre { satisfaccion: number | null; }

/** Cierre de la consulta con encuesta opcional de satisfacción (KPI OE4: promedio > 8/10). */
@Component({
  selector: 'lf-cierre',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <dialog #d class="modal" aria-labelledby="cierre-titulo">
      <div class="modal-body">
        <h2 id="cierre-titulo">Finalizar consulta</h2>
        @if (!hayElegido()) {
          <p class="nota"><lf-icon name="alert" [size]="16" /> Aún no se eligió ningún look. Puedes cerrar igual, pero no contará como decisión.</p>
        }
        <div>
          <p>Pregunta al cliente: <strong>¿Qué tan útil le fue ver su look antes del servicio?</strong></p>
          <p class="subtle">Opcional · 1 = nada útil, 10 = muy útil</p>
        </div>
        <div class="escala" role="radiogroup" aria-label="Satisfacción de 1 a 10">
          @for (n of escala; track n) {
            <button type="button" role="radio" [attr.aria-checked]="nota() === n" (click)="nota.set(nota() === n ? null : n)">{{ n }}</button>
          }
        </div>
        <p class="subtle">Al finalizar se elimina la foto del servidor y se apaga la cámara.</p>
      </div>
      <div class="modal-foot">
        <button class="btn btn-secondary" (click)="responder(null)">Volver</button>
        <button class="btn btn-primary" (click)="responder({ satisfaccion: nota() })">Finalizar y borrar foto</button>
      </div>
    </dialog>
  `,
  styles: `
    .nota { display: flex; gap: 8px; align-items: flex-start; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--warn-soft); color: var(--warn); font-size: 14px; }
    .escala { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; }
    .escala button { height: 40px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface); font-weight: 600; cursor: pointer; color: var(--text-2); }
    .escala button:hover { border-color: var(--border-strong); color: var(--text); }
    .escala button[aria-checked="true"] { background: var(--text); border-color: var(--text); color: #fff; }
  `,
})
export class CierreDialog extends Dialogo<Cierre | null> {
  protected readonly ref = viewChild.required<ElementRef<HTMLDialogElement>>('d');
  protected readonly nota = signal<number | null>(null);
  protected readonly hayElegido = signal(false);
  protected readonly escala = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  pedir(hayElegido: boolean): Promise<Cierre | null> {
    this.nota.set(null);
    this.hayElegido.set(hayElegido);
    return this.abrirCon(null);
  }
  protected override responder(v: Cierre | null) { super.responder(v); }
}
