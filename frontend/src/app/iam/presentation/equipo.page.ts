import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { mensajeDe } from '@core/errors/app-error';
import { EquipoService } from '@iam/application/equipo.service';
import { SesionStore } from '@iam/application/sesion.store';
import { etiquetaRol, iniciales, NuevoUsuario, Usuario } from '@iam/domain/usuario';
import { IconComponent } from '@shared/ui/icon.component';
import { ToastService } from '@shared/ui/toast.service';

const VACIO: NuevoUsuario = { nombre: '', email: '', password: '', rol: 'estilista' };

@Component({
  selector: 'lf-equipo-page',
  imports: [FormsModule, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <header class="page-head">
        <div>
          <p class="eyebrow">Administración</p>
          <h1>Equipo</h1>
          <p class="muted">Cuentas del personal que atiende consultas. Los clientes no necesitan cuenta.</p>
        </div>
      </header>

      <div class="grid">
        <section class="card">
          <table class="table">
            <thead><tr><th>Persona</th><th>Rol</th><th>Estado</th><th></th></tr></thead>
            <tbody>
              @for (u of usuarios(); track u.id) {
                <tr [class.inactive]="!u.activo">
                  <td>
                    <div class="persona">
                      <span class="avatar">{{ iniciales(u.nombre) }}</span>
                      <div><strong>{{ u.nombre }}</strong>@if (u.id === yo()?.id) { <span class="subtle"> · tú</span> }<div class="subtle">{{ u.email }}</div></div>
                    </div>
                  </td>
                  <td>{{ etiquetaRol(u.rol) }}</td>
                  <td><span class="badge" [class.ok]="u.activo"><span class="dot"></span>{{ u.activo ? 'Activo' : 'Inactivo' }}</span></td>
                  <td class="acciones">
                    @if (u.id !== yo()?.id) {
                      <button class="btn btn-ghost btn-sm" (click)="alternar(u)">{{ u.activo ? 'Desactivar' : 'Activar' }}</button>
                    }
                  </td>
                </tr>
              } @empty {
                <tr><td colspan="4" class="subtle">Cargando…</td></tr>
              }
            </tbody>
          </table>
        </section>

        <form class="card card-pad stack" (ngSubmit)="crear()">
          <div><h2>Nueva cuenta</h2><p class="subtle">Comparte la contraseña temporal en persona.</p></div>
          <label class="field">Nombre completo<input class="input" name="nombre" [(ngModel)]="nuevo.nombre" required /></label>
          <label class="field">Correo<input class="input" type="email" name="email" [(ngModel)]="nuevo.email" required /></label>
          <label class="field">Contraseña temporal<input class="input" type="password" name="password" minlength="8" [(ngModel)]="nuevo.password" required /></label>
          <label class="field">Rol
            <select class="select" name="rol" [(ngModel)]="nuevo.rol">
              <option value="estilista">Estilista</option>
              <option value="admin">Administrador</option>
            </select>
          </label>
          <button class="btn btn-primary" [disabled]="guardando()"><lf-icon name="plus" /> Crear cuenta</button>
        </form>
      </div>
    </div>
  `,
  styles: `
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 20px; align-items: start; }
    .card:first-child { padding: 16px 8px 4px; overflow-x: auto; }
    .persona { display: flex; gap: 12px; align-items: center; }
    .avatar { width: 34px; height: 34px; border-radius: 50%; background: var(--accent-soft); color: var(--accent); display: grid; place-items: center; font-size: 13px; font-weight: 600; flex-shrink: 0; }
    .acciones { text-align: right; }
    @media (max-width: 960px) { .grid { grid-template-columns: 1fr; } }
  `,
})
export class EquipoPage implements OnInit {
  private readonly equipo = inject(EquipoService);
  private readonly toast = inject(ToastService);
  protected readonly yo = inject(SesionStore).usuario;
  protected readonly usuarios = signal<Usuario[]>([]);
  protected readonly guardando = signal(false);
  protected nuevo: NuevoUsuario = { ...VACIO };
  protected readonly etiquetaRol = etiquetaRol;
  protected readonly iniciales = iniciales;

  ngOnInit() { this.cargar(); }

  async cargar() {
    try { this.usuarios.set(await this.equipo.listar()); } catch (e) { this.toast.error(mensajeDe(e)); }
  }

  async crear() {
    this.guardando.set(true);
    try {
      const u = await this.equipo.registrar(this.nuevo);
      this.nuevo = { ...VACIO };
      this.toast.ok(`Cuenta creada para ${u.nombre}.`);
      await this.cargar();
    } catch (e) {
      this.toast.error(mensajeDe(e));
    } finally {
      this.guardando.set(false);
    }
  }

  async alternar(u: Usuario) {
    try { await this.equipo.cambiarEstado(u, !u.activo); await this.cargar(); } catch (e) { this.toast.error(mensajeDe(e)); }
  }
}
