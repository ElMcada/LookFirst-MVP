import { ChangeDetectionStrategy, Component, ElementRef, signal, viewChild } from '@angular/core';
import { VERSION_CONSENTIMIENTO } from '@consulta/domain/consulta';
import { Dialogo } from '@shared/ui/dialogo';
import { IconComponent } from '@shared/ui/icon.component';

/** Consentimiento informado del cliente (REQ-09, Ley N.° 29733). */
@Component({
  selector: 'lf-consentimiento',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <dialog #d class="modal" aria-labelledby="cons-titulo">
      <div class="modal-body">
        <span class="icono"><lf-icon name="shield" [size]="22" /></span>
        <div>
          <h2 id="cons-titulo">Antes de usar la cámara</h2>
          <p class="muted">Lee esto con el cliente. Conforme a la Ley N.° 29733 de Protección de Datos Personales:</p>
        </div>
        <ul>
          <li>Su foto se usa <strong>solo durante esta consulta</strong>, para detectar rostro y cabello.</li>
          <li>Para generar los looks con IA se envía a un servicio de inferencia que no la conserva.</li>
          <li><strong>Nunca se guarda</strong> en una base de datos: se elimina al finalizar, al retirar el consentimiento o a los 30 minutos.</li>
          <li>Solo registramos datos anónimos de uso (qué looks se probaron y cuánto tardaron).</li>
          <li>Puede retirar su consentimiento en cualquier momento.</li>
        </ul>
        <label class="check acepto">
          <input type="checkbox" [checked]="acepta()" (change)="acepta.set($any($event.target).checked)" />
          El cliente entiende y autoriza el tratamiento temporal de su imagen facial.
        </label>
        <p class="subtle">Versión {{ version }}</p>
      </div>
      <div class="modal-foot">
        <button class="btn btn-secondary" (click)="responder(false)">No acepta</button>
        <button class="btn btn-primary" [disabled]="!acepta()" (click)="responder(true)">Aceptar y activar cámara</button>
      </div>
    </dialog>
  `,
  styles: `
    .icono { width: 44px; height: 44px; border-radius: 12px; background: var(--accent-soft); color: var(--accent); display: grid; place-items: center; }
    ul { margin: 0; padding-left: 18px; display: grid; gap: 8px; color: var(--text-2); font-size: 14px; }
    strong { color: var(--text); font-weight: 600; }
    .acepto { padding: 14px; border: 1px solid var(--border); border-radius: var(--radius); align-items: flex-start; line-height: 1.4; }
    .acepto input { margin-top: 2px; flex-shrink: 0; }
  `,
})
export class ConsentimientoDialog extends Dialogo<boolean> {
  protected readonly ref = viewChild.required<ElementRef<HTMLDialogElement>>('d');
  protected readonly acepta = signal(false);
  protected readonly version = VERSION_CONSENTIMIENTO;

  pedir(): Promise<boolean> {
    this.acepta.set(false);
    return this.abrirCon(false);
  }
  protected override responder(v: boolean) { super.responder(v); }
}
