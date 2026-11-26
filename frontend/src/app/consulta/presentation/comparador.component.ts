import { ChangeDetectionStrategy, Component, input, signal } from '@angular/core';
import { IconComponent } from '@shared/ui/icon.component';

/** Comparador antes/después con deslizador (REQ-08). Accesible con teclado vía <input type=range>. */
@Component({
  selector: 'lf-comparador',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="comparador">
      <img [src]="despues()" alt="Después" />
      <img [src]="antes()" alt="Antes" class="antes" [style.clip-path]="'inset(0 ' + (100 - pos()) + '% 0 0)'" />
      <span class="etiqueta izq">Antes</span>
      <span class="etiqueta der">Después</span>
      <div class="linea" [style.left.%]="pos()"><span class="mango"><lf-icon name="grip" [size]="16" /></span></div>
      <input type="range" min="0" max="100" [value]="pos()" (input)="mover($event)" aria-label="Comparar antes y después" />
    </div>
  `,
  styles: `
    :host { display: block; position: absolute; inset: 0; }
    .comparador { position: absolute; inset: 0; user-select: none; }
    img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    .etiqueta { position: absolute; top: 14px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;
      background: rgb(24 23 26 / .6); color: #fff; backdrop-filter: blur(6px); pointer-events: none; }
    .izq { left: 14px; } .der { right: 14px; background: rgb(255 255 255 / .85); color: var(--text); }
    .linea { position: absolute; top: 0; bottom: 0; width: 2px; background: #fff; transform: translateX(-1px); pointer-events: none; box-shadow: 0 0 0 1px rgb(0 0 0 / .08); }
    .mango { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 36px; height: 36px; border-radius: 50%;
      background: #fff; color: var(--text); display: grid; place-items: center; box-shadow: var(--shadow); }
    input { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: ew-resize; }
    input:focus-visible + .linea, .comparador:focus-within .mango { outline: 2px solid var(--accent); }
  `,
})
export class ComparadorComponent {
  readonly antes = input.required<string>();
  readonly despues = input.required<string>();
  protected readonly pos = signal(50);
  protected mover(e: Event) { this.pos.set(+(e.target as HTMLInputElement).value); }
}
