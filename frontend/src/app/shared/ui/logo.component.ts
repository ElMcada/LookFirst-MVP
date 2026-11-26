import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'lf-logo',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="logo" [class.inverso]="inverso()">
      <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
        <rect width="32" height="32" rx="8" class="fondo" />
        <path d="M11 9v14h10" fill="none" class="trazo" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="22" cy="11" r="2.4" fill="#8f86ff" />
      </svg>
      <span>LookFirst</span>
    </span>
  `,
  styles: `
    .logo { display: inline-flex; align-items: center; gap: 10px; font-weight: 650; font-size: 17px; letter-spacing: -0.01em; }
    .fondo { fill: var(--text); } .trazo { stroke: #fff; }
    .inverso .fondo { fill: #fff; } .inverso .trazo { stroke: var(--text); }
  `,
})
export class LogoComponent {
  readonly inverso = input(false);
}
