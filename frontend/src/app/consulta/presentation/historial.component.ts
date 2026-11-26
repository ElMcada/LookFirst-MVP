import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { Look } from '@consulta/domain/consulta';
import { IconComponent } from '@shared/ui/icon.component';

/** Looks probados en la consulta: se puede volver a comparar cualquiera. */
@Component({
  selector: 'lf-historial',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (looks().length) {
      <div class="cabecera"><h3>Looks probados</h3><span class="subtle">{{ looks().length }}</span></div>
      <div class="tira">
        @for (l of looks(); track l.id) {
          <button type="button" class="mini" [class.actual]="l.id === actualId()" [attr.aria-pressed]="l.id === actualId()"
                  [title]="l.etiqueta" [disabled]="deshabilitado()" (click)="ver.emit(l)">
            <img [src]="l.imagenUrl" [alt]="l.etiqueta" />
            @if (l.id === elegidoId()) { <span class="elegido"><lf-icon name="check" [size]="12" /></span> }
            <span class="nombre">{{ l.etiqueta }}</span>
          </button>
        }
      </div>
    }
  `,
  styles: `
    .cabecera { display: flex; align-items: baseline; gap: 8px; margin: 20px 0 10px; }
    .tira { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }
    .mini { position: relative; flex: 0 0 104px; padding: 0; border: 0; background: none; cursor: pointer; text-align: left; }
    .mini img { width: 104px; height: 78px; object-fit: cover; border-radius: var(--radius-sm); box-shadow: 0 0 0 1px var(--border); transition: box-shadow .15s; }
    .mini:hover img { box-shadow: 0 0 0 1px var(--border-strong); }
    .mini.actual img { box-shadow: 0 0 0 2px var(--text); }
    .nombre { display: block; margin-top: 6px; font-size: 12px; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .elegido { position: absolute; top: 6px; right: 6px; width: 20px; height: 20px; border-radius: 50%; background: var(--ok); color: #fff; display: grid; place-items: center; }
  `,
})
export class HistorialComponent {
  readonly looks = input.required<Look[]>();
  readonly actualId = input<string | null>(null);
  readonly elegidoId = input<string | null>(null);
  readonly deshabilitado = input(false);
  readonly ver = output<Look>();
}
