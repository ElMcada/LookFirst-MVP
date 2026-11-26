import { ChangeDetectionStrategy, Component, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ReconocedorVoz } from '@consulta/application/puertos';
import { MAX_INSTRUCCION } from '@consulta/domain/consulta';
import { IconComponent } from '@shared/ui/icon.component';

export interface Pedido { texto: string; origen: 'texto' | 'voz'; }

const EJEMPLOS = ['Bob a la mandíbula rubio ceniza', 'Largo con ondas y capas', 'Mechas californianas color miel'];

/** Pedido en lenguaje natural por texto o voz (REQ-06). */
@Component({
  selector: 'lf-solicitud',
  imports: [FormsModule, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form class="caja" [class.escuchando]="voz.escuchando()" (ngSubmit)="enviar('texto')">
      <input class="campo" name="texto" [ngModel]="texto()" (ngModelChange)="texto.set($event)" [maxlength]="max" [disabled]="deshabilitado()"
             [placeholder]="voz.escuchando() ? 'Escuchando…' : 'Describe el look que quiere el cliente'" aria-label="Pedido del cliente" />
      <button type="button" class="btn btn-ghost btn-icon" [class.activo]="voz.escuchando()" [disabled]="deshabilitado()"
              (click)="hablar()" [attr.aria-pressed]="voz.escuchando()" [attr.aria-label]="voz.escuchando() ? 'Detener micrófono' : 'Dictar por voz'">
        <lf-icon name="mic" />
      </button>
      <button class="btn btn-primary btn-icon" [disabled]="deshabilitado() || !texto().trim()" aria-label="Simular">
        <lf-icon name="send" />
      </button>
    </form>
    <div class="ejemplos">
      @for (e of ejemplos; track e) {
        <button type="button" class="chip" [disabled]="deshabilitado()" (click)="usarEjemplo(e)">{{ e }}</button>
      }
    </div>
    @if (!voz.soportado) { <p class="subtle">El dictado por voz funciona en Chrome y Edge.</p> }
    @if (errorVoz()) { <p class="form-error">{{ errorVoz() }}</p> }
  `,
  styles: `
    .caja { display: flex; align-items: center; gap: 4px; padding: 4px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); transition: border-color .15s, box-shadow .15s; }
    .caja:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
    .caja.escuchando { border-color: var(--accent); }
    .campo { flex: 1; min-width: 0; height: 40px; padding: 0 10px; border: 0; background: none; font-size: 14px; outline: none; }
    .campo::placeholder { color: var(--text-3); }
    .activo { background: var(--accent-soft); color: var(--accent); animation: latido 1.2s ease-in-out infinite; }
    @keyframes latido { 50% { box-shadow: 0 0 0 6px var(--accent-soft); } }
    .ejemplos { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .chip { height: 28px; padding: 0 10px; border-radius: 999px; border: 1px solid var(--border); background: none; font-size: 12px; color: var(--text-2); cursor: pointer; }
    .chip:hover:not(:disabled) { border-color: var(--border-strong); color: var(--text); }
    .chip:disabled { opacity: .5; cursor: not-allowed; }
    p { margin-top: 8px; }
  `,
})
export class SolicitudComponent {
  protected readonly voz = inject(ReconocedorVoz);
  readonly deshabilitado = input(false);
  readonly pedir = output<Pedido>();
  protected readonly texto = signal('');
  protected readonly errorVoz = signal('');
  protected readonly max = MAX_INSTRUCCION;
  protected readonly ejemplos = EJEMPLOS;

  enviar(origen: Pedido['origen']) {
    const t = this.texto().trim();
    if (t) this.pedir.emit({ texto: t, origen });
  }

  usarEjemplo(e: string) {
    this.texto.set(e);
    this.enviar('texto');
  }

  hablar() {
    this.errorVoz.set('');
    if (this.voz.escuchando()) return this.voz.detener();
    this.voz.escuchar({
      alResultado: (t) => { this.texto.set(t); this.enviar('voz'); },
      alError: (m) => this.errorVoz.set(m),
    });
  }
}
