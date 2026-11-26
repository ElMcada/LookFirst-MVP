import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { Paso, PASOS } from '@consulta/domain/consulta';
import { IconComponent } from '@shared/ui/icon.component';

@Component({
  selector: 'lf-stepper',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ol class="stepper" aria-label="Progreso de la consulta">
      @for (p of pasos; track p.id; let i = $index) {
        <li [class.hecho]="i < indice()" [class.actual]="i === indice()" [attr.aria-current]="i === indice() ? 'step' : null">
          <span class="num">@if (i < indice()) { <lf-icon name="check" [size]="14" /> } @else { {{ i + 1 }} }</span>
          <span class="txt">{{ p.texto }}</span>
        </li>
      }
    </ol>
  `,
  styles: `
    .stepper { list-style: none; margin: 0 0 24px; padding: 0; display: flex; gap: 8px; flex-wrap: wrap; }
    li { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-3); font-weight: 550; }
    li:not(:last-child)::after { content: ""; width: 32px; height: 1px; background: var(--border-strong); margin-left: 4px; }
    .num { width: 22px; height: 22px; border-radius: 50%; display: grid; place-items: center; font-size: 12px; border: 1px solid var(--border-strong); background: var(--surface); }
    .actual { color: var(--text); } .actual .num { background: var(--text); border-color: var(--text); color: #fff; }
    .hecho { color: var(--text-2); } .hecho .num { background: var(--ok-soft); border-color: transparent; color: var(--ok); }
  `,
})
export class StepperComponent {
  readonly paso = input.required<Paso>();
  protected readonly pasos = PASOS;
  protected readonly indice = computed(() => PASOS.findIndex((p) => p.id === this.paso()));
}
