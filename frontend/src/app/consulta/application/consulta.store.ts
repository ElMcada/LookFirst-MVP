import { computed, inject, Injectable, signal } from '@angular/core';
import { AppError } from '@core/errors/app-error';
import { Estilo } from '@catalogo/domain/estilo';
import {
  aLook, AnalisisRostro, Look, Origen, pasoActual, validarInstruccion, VERSION_CONSENTIMIENTO,
} from '@consulta/domain/consulta';
import { ConsultaRepository } from './puertos';

/** Estado y casos de uso de la consulta en el sillón. No conoce el DOM. */
@Injectable({ providedIn: 'root' })
export class ConsultaStore {
  private readonly repo = inject(ConsultaRepository);

  readonly consultaId = signal<string | null>(null);
  readonly analisis = signal<AnalisisRostro | null>(null);
  readonly fotoUrl = signal<string | null>(null);
  readonly looks = signal<Look[]>([]);
  readonly actualId = signal<string | null>(null);
  readonly elegidoId = signal<string | null>(null);
  /** Texto de la tarea en curso (null = libre). */
  readonly ocupado = signal<string | null>(null);

  readonly activa = computed(() => this.consultaId() !== null);
  readonly lookActual = computed(() => this.looks().find((l) => l.id === this.actualId()) ?? null);
  readonly lookElegido = computed(() => this.looks().find((l) => l.id === this.elegidoId()) ?? null);
  readonly paso = computed(() =>
    pasoActual({ activa: this.activa(), conFoto: this.analisis() !== null, elegido: this.elegidoId() !== null }));

  iniciar(): Promise<void> {
    return this.tarea('Iniciando consulta…', async () => {
      const { id } = await this.repo.iniciar(VERSION_CONSENTIMIENTO);
      this.limpiar();
      this.consultaId.set(id);
    });
  }

  analizarFoto(foto: Blob): Promise<void> {
    return this.tarea('Analizando el rostro…', async () => {
      const analisis = await this.repo.subirFoto(this.requerir(), foto);
      this.revocarUrl();
      this.fotoUrl.set(URL.createObjectURL(foto)); // la foto original solo vive en memoria del navegador
      this.analisis.set(analisis);
      this.looks.set([]);       // los looks de la foto anterior ya no aplican
      this.actualId.set(null);
      this.elegidoId.set(null);
    });
  }

  simularEstilo(estilo: Estilo): Promise<void> {
    return this.simular('catalogo', { estilo_id: estilo.id });
  }

  simularInstruccion(texto: string, origen: Exclude<Origen, 'catalogo'>): Promise<void> {
    const error = validarInstruccion(texto);
    if (error) return Promise.reject(new AppError(error));
    return this.simular(origen, { instruccion: texto.trim() });
  }

  ver(look: Look): void {
    if (!this.ocupado()) this.actualId.set(look.id);
  }

  elegir(look: Look): Promise<void> {
    return this.tarea('Guardando la elección…', async () => {
      await this.repo.elegir(this.requerir(), look.id);
      this.elegidoId.set(look.id);
      this.actualId.set(look.id);
    });
  }

  finalizar(satisfaccion: number | null): Promise<void> {
    return this.tarea('Cerrando consulta…', async () => {
      await this.repo.finalizar(this.requerir(), satisfaccion);
      this.limpiar();
    });
  }

  revocar(): Promise<void> {
    return this.tarea('Eliminando datos…', async () => {
      await this.repo.revocar(this.requerir());
      this.limpiar();
    });
  }

  /** Al cerrar la pestaña o la sesión: el servidor borra la foto de inmediato. */
  cerrarAlSalir(): void {
    const id = this.consultaId();
    if (id) this.repo.finalizarAlSalir(id);
    this.limpiar();
  }

  private simular(origen: Origen, datos: { estilo_id?: string; instruccion?: string }): Promise<void> {
    return this.tarea('Generando el nuevo look…', async () => {
      if (!this.analisis()) throw new AppError('Primero captura o sube una foto.');
      const look = aLook(await this.repo.simular(this.requerir(), { origen, ...datos }), origen);
      this.looks.update((ls) => [look, ...ls]);
      this.actualId.set(look.id);
    });
  }

  private async tarea(texto: string, fn: () => Promise<void>): Promise<void> {
    if (this.ocupado()) return;
    this.ocupado.set(texto);
    try {
      await fn();
    } catch (e) {
      // 409: la consulta ya se cerró o venció en el servidor; se descarta también aquí
      if (e instanceof AppError && e.status === 409 && this.activa()) this.limpiar();
      throw e;
    } finally {
      this.ocupado.set(null);
    }
  }

  private requerir(): string {
    const id = this.consultaId();
    if (!id) throw new AppError('No hay una consulta activa.');
    return id;
  }

  private revocarUrl() {
    const url = this.fotoUrl();
    if (url) URL.revokeObjectURL(url);
  }

  private limpiar() {
    this.revocarUrl();
    this.consultaId.set(null);
    this.analisis.set(null);
    this.fotoUrl.set(null);
    this.looks.set([]);
    this.actualId.set(null);
    this.elegidoId.set(null);
  }
}
