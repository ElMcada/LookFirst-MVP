import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { Estilo, fondoMuestra } from '@catalogo/domain/estilo';
import { IconComponent } from '@shared/ui/icon.component';

/** Estilo recomendado que el estilista puede simular con un clic. */
@Component({
  selector: 'lf-estilo-item',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button class="item" type="button" [disabled]="deshabilitado()" (click)="elegir.emit(estilo())">
      <span class="swatch" [style.background]="fondo()"></span>
      <span class="texto">
        <span class="nombre">{{ estilo().nombre }}</span>
        <span class="desc">{{ estilo().descripcion }}</span>
      </span>
      <span class="badge">{{ estilo().tipo === 'tinte' ? 'Tinte' : 'Corte' }}</span>
      <lf-icon class="flecha" name="send" [size]="16" />
    </button>
  `,
  styles: `
    .item { width: 100%; display: flex; align-items: center; gap: 12px; padding: 12px; text-align: left; cursor: pointer;
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); transition: border-color .15s, background .15s; }
    .item:hover:not(:disabled) { border-color: var(--border-strong); background: var(--surface-2); }
    .item:hover:not(:disabled) .flecha { color: var(--text); transform: translateX(2px); }
    .item:disabled { opacity: .5; cursor: not-allowed; }
    .texto { flex: 1; min-width: 0; display: grid; gap: 2px; }
    .nombre { font-weight: 600; font-size: 14px; }
    .desc { font-size: 13px; color: var(--text-2); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .flecha { color: var(--text-3); transition: transform .15s, color .15s; }
  `,
})
export class EstiloItemComponent {
  readonly estilo = input.required<Estilo>();
  readonly deshabilitado = input(false);
  readonly elegir = output<Estilo>();
  protected readonly fondo = computed(() => fondoMuestra(this.estilo()));
}
