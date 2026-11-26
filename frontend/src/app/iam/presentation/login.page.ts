import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { mensajeDe } from '@core/errors/app-error';
import { SesionStore } from '@iam/application/sesion.store';
import { IconComponent } from '@shared/ui/icon.component';
import { LogoComponent } from '@shared/ui/logo.component';

@Component({
  selector: 'lf-login-page',
  imports: [FormsModule, IconComponent, LogoComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="split">
      <aside class="brand">
        <lf-logo [inverso]="true" />
        <div class="claim">
          <h1>Pruébalo antes<br />de cortarlo.</h1>
          <p>Simula cortes y tintes sobre el rostro real del cliente y alinea expectativas antes de tomar las tijeras.</p>
        </div>
        <ul>
          <li><lf-icon name="face" /> Recomendaciones según la forma del rostro</li>
          <li><lf-icon name="mic" /> Pedidos por voz o texto, en español</li>
          <li><lf-icon name="shield" /> Fotos que nunca se guardan (Ley N.° 29733)</li>
        </ul>
      </aside>

      <main class="panel">
        <form class="form" (ngSubmit)="ingresar()" novalidate>
          <div>
            <h2 class="titulo">Inicia sesión</h2>
            <p class="muted">Acceso exclusivo para el personal del salón.</p>
          </div>
          @if (expirada) {
            <p class="aviso"><lf-icon name="clock" [size]="16" /> Tu sesión expiró. Vuelve a ingresar.</p>
          }
          <label class="field">Correo
            <input class="input" type="email" name="email" autocomplete="username" [(ngModel)]="email" required autofocus />
          </label>
          <label class="field">Contraseña
            <input class="input" type="password" name="password" autocomplete="current-password" [(ngModel)]="password" required />
          </label>
          <p class="form-error" role="alert">{{ error() }}</p>
          <button class="btn btn-primary btn-lg btn-block" [disabled]="cargando()">
            {{ cargando() ? 'Ingresando…' : 'Ingresar' }}
          </button>
        </form>
      </main>
    </div>
  `,
  styles: `
    .split { min-height: 100vh; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
    .brand { background: var(--text); color: #fff; padding: 40px 56px; display: flex; flex-direction: column; justify-content: space-between; gap: 40px; }
    .claim h1 { font-size: 44px; letter-spacing: -0.03em; line-height: 1.05; }
    .claim p { margin-top: 16px; max-width: 420px; color: rgb(255 255 255 / .65); font-size: 16px; }
    ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; color: rgb(255 255 255 / .8); }
    li { display: flex; gap: 12px; align-items: center; }
    li lf-icon { color: #b3abff; }
    .panel { display: grid; place-items: center; padding: 32px; }
    .form { width: 100%; max-width: 360px; display: grid; gap: 18px; }
    .titulo { font-size: 24px; margin-bottom: 4px; }
    .aviso { display: flex; gap: 8px; align-items: center; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--warn-soft); color: var(--warn); font-size: 14px; }
    @media (max-width: 860px) { .split { grid-template-columns: 1fr; } .brand { display: none; } }
  `,
})
export class LoginPage {
  private readonly sesion = inject(SesionStore);
  private readonly router = inject(Router);
  protected readonly expirada = inject(ActivatedRoute).snapshot.queryParamMap.has('expirada');
  protected email = '';
  protected password = '';
  protected readonly error = signal('');
  protected readonly cargando = signal(false);

  async ingresar() {
    this.error.set('');
    this.cargando.set(true);
    try {
      await this.sesion.iniciar(this.email, this.password);
      this.router.navigateByUrl('/consulta');
    } catch (e) {
      this.error.set(mensajeDe(e));
    } finally {
      this.cargando.set(false);
    }
  }
}
