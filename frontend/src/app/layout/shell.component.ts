import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Camara } from '@consulta/application/puertos';
import { ConsultaStore } from '@consulta/application/consulta.store';
import { SesionStore } from '@iam/application/sesion.store';
import { etiquetaRol, iniciales } from '@iam/domain/usuario';
import { IconComponent } from '@shared/ui/icon.component';
import { LogoComponent } from '@shared/ui/logo.component';

@Component({
  selector: 'lf-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent, LogoComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="barra">
      <div class="interior">
        <a routerLink="/consulta" class="marca" aria-label="LookFirst, inicio"><lf-logo /></a>
        <nav aria-label="Principal">
          <a routerLink="/consulta" routerLinkActive="activo"><lf-icon name="sparkles" [size]="16" /> Consulta</a>
          <a routerLink="/indicadores" routerLinkActive="activo"><lf-icon name="chart" [size]="16" /> Indicadores</a>
          @if (sesion.esAdmin()) {
            <a routerLink="/catalogo" routerLinkActive="activo"><lf-icon name="scissors" [size]="16" /> Catálogo</a>
            <a routerLink="/equipo" routerLinkActive="activo"><lf-icon name="users" [size]="16" /> Equipo</a>
          }
        </nav>
        <span class="spacer"></span>
        @if (consulta.activa()) {
          <span class="badge accent en-curso"><span class="dot"></span> Consulta en curso</span>
        }
        @if (sesion.usuario(); as u) {
          <div class="usuario">
            <span class="avatar">{{ iniciales(u.nombre) }}</span>
            <span class="quien"><strong>{{ u.nombre }}</strong><span>{{ etiquetaRol(u.rol) }}</span></span>
          </div>
        }
        <button class="btn btn-ghost btn-icon" (click)="salir()" aria-label="Cerrar sesión" title="Cerrar sesión"><lf-icon name="logout" /></button>
      </div>
    </header>
    <main><router-outlet /></main>
  `,
  styles: `
    .barra { position: sticky; top: 0; z-index: 20; background: rgb(247 247 245 / .85); backdrop-filter: saturate(1.4) blur(12px); border-bottom: 1px solid var(--border); }
    .interior { max-width: 1240px; margin: 0 auto; height: 64px; padding: 0 24px; display: flex; align-items: center; gap: 24px; }
    .marca { text-decoration: none; }
    nav { display: flex; gap: 2px; }
    nav a { display: inline-flex; align-items: center; gap: 8px; height: 36px; padding: 0 12px; border-radius: var(--radius-sm);
      text-decoration: none; font-size: 14px; font-weight: 550; color: var(--text-2); transition: background .15s, color .15s; }
    nav a:hover { color: var(--text); background: var(--surface-2); }
    nav a.activo { color: var(--text); background: var(--surface); box-shadow: inset 0 0 0 1px var(--border); }
    .usuario { display: flex; align-items: center; gap: 10px; }
    .avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--text); color: #fff; display: grid; place-items: center; font-size: 12px; font-weight: 600; }
    .quien { display: grid; line-height: 1.2; font-size: 13px; } .quien span { color: var(--text-3); font-size: 12px; }
    @media (max-width: 900px) { .quien, .en-curso { display: none; } nav a { padding: 0 10px; } .interior { gap: 12px; } }
    @media (max-width: 680px) { nav a { font-size: 0; gap: 0; } }
  `,
})
export class ShellComponent {
  protected readonly sesion = inject(SesionStore);
  protected readonly consulta = inject(ConsultaStore);
  private readonly camara = inject(Camara);
  private readonly router = inject(Router);
  protected readonly iniciales = iniciales;
  protected readonly etiquetaRol = etiquetaRol;

  salir() {
    this.consulta.cerrarAlSalir(); // borra la foto en el servidor si había una consulta abierta
    this.camara.detener();
    this.sesion.cerrar();
    this.router.navigateByUrl('/login');
  }
}
