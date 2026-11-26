import { computed, inject, Injectable, signal } from '@angular/core';
import { AppError } from '@core/errors/app-error';
import { esAdmin, Sesion } from '@iam/domain/usuario';
import { AlmacenSesion, IamRepository } from './iam.repository';

/** Estado de la sesión del personal (casos de uso: iniciar, verificar y cerrar sesión). */
@Injectable({ providedIn: 'root' })
export class SesionStore {
  private readonly repo = inject(IamRepository);
  private readonly almacen = inject(AlmacenSesion);
  private readonly sesion = signal<Sesion | null>(this.almacen.leer());
  private verificada = false;

  readonly usuario = computed(() => this.sesion()?.usuario ?? null);
  readonly token = computed(() => this.sesion()?.token ?? null);
  readonly autenticado = computed(() => this.sesion() !== null);
  readonly esAdmin = computed(() => esAdmin(this.usuario()));

  async iniciar(email: string, password: string): Promise<void> {
    if (!email.trim() || !password) throw new AppError('Ingresa tu correo y contraseña.');
    const s = await this.repo.login(email.trim(), password);
    this.almacen.guardar(s);
    this.sesion.set(s);
    this.verificada = true;
  }

  /** Confirma una sola vez con el servidor que el token guardado sigue siendo válido. */
  async verificar(): Promise<boolean> {
    const s = this.sesion();
    if (!s) return false;
    if (this.verificada) return true;
    try {
      const usuario = await this.repo.yo();
      const fresca = { token: s.token, usuario };
      this.almacen.guardar(fresca);
      this.sesion.set(fresca);
      this.verificada = true;
      return true;
    } catch {
      this.cerrar();
      return false;
    }
  }

  cerrar(): void {
    this.almacen.borrar();
    this.sesion.set(null);
    this.verificada = false;
  }
}
