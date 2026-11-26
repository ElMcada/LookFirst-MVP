import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { IconComponent } from './icon.component';
import { ToastService } from './toast.service';

@Component({
  selector: 'lf-toasts',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="toasts" role="status" aria-live="polite">
      @for (t of servicio.toasts(); track t.id) {
        <div class="toast" [class]="'toast ' + t.tipo">
          <lf-icon [name]="t.tipo === 'ok' ? 'check' : t.tipo === 'error' ? 'alert' : 'info'" />
          <span>{{ t.texto }}</span>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="servicio.cerrar(t.id)" aria-label="Cerrar aviso">
            <lf-icon name="x" [size]="16" />
          </button>
        </div>
      }
    </div>
  `,
  styles: `
    .toasts { position: fixed; right: 20px; bottom: 20px; z-index: 100; display: grid; gap: 8px; width: min(420px, calc(100vw - 40px)); }
    .toast { display: flex; align-items: flex-start; gap: 10px; padding: 12px 8px 12px 14px; background: var(--text); color: #fff;
      border-radius: var(--radius); box-shadow: var(--shadow-lg); font-size: 14px; animation: aparecer .2s var(--ease); }
    .toast span { flex: 1; padding-top: 1px; }
    .toast.ok lf-icon { color: #7ee2b0; } .toast.error lf-icon { color: #ffb4a8; } .toast.info lf-icon { color: #c4beff; }
    .toast .btn { color: #fff; height: 24px; width: 24px; } .toast .btn:hover { background: rgb(255 255 255 / .12); color: #fff; }
  `,
})
export class ToastsComponent {
  protected readonly servicio = inject(ToastService);
}
