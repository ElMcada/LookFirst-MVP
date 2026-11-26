import { TestBed } from '@angular/core/testing';
import { AppError } from '@core/errors/app-error';
import { AnalisisRostro, SimulacionDto } from '@consulta/domain/consulta';
import { ConsultaStore } from './consulta.store';
import { ConsultaRepository, PedidoSimulacion } from './puertos';

class RepoFalso extends ConsultaRepository {
  llamadas: string[] = [];
  n = 0;
  fallarCon: AppError | null = null;
  async iniciar() { this.llamadas.push('iniciar'); return { id: 'c1' }; }
  async subirFoto(): Promise<AnalisisRostro> {
    return { forma_rostro: 'ovalado', metricas: { alto_ancho: 1.3, mandibula_pomulos: 0.8, frente_pomulos: 0.9 }, razon: '', recomendaciones: [] };
  }
  async simular(_id: string, p: PedidoSimulacion): Promise<SimulacionDto> {
    if (this.fallarCon) throw this.fallarCon;
    this.llamadas.push(`simular:${p.origen}`);
    return { id: `s${++this.n}`, etiqueta: p.instruccion ?? 'Bob', imagen_b64: 'AA', latencia_s: 7.2, modo: 'respaldo_local', tipo_corte: 'medio', fuente_prompt: 'llm', prompt_en: 'x', aviso: null };
  }
  async elegir(_: string, s: string) { this.llamadas.push(`elegir:${s}`); }
  async finalizar(_: string, sat: number | null) { this.llamadas.push(`finalizar:${sat}`); }
  async revocar() { this.llamadas.push('revocar'); }
  finalizarAlSalir() { this.llamadas.push('salir'); }
}

describe('ConsultaStore', () => {
  let store: ConsultaStore;
  let repo: RepoFalso;

  beforeEach(() => {
    URL.createObjectURL = () => 'blob:foto';
    URL.revokeObjectURL = () => {};
    repo = new RepoFalso();
    TestBed.configureTestingModule({ providers: [{ provide: ConsultaRepository, useValue: repo }] });
    store = TestBed.inject(ConsultaStore);
  });

  it('avanza por los pasos de la consulta', async () => {
    expect(store.paso()).toBe('consentimiento');
    await store.iniciar();
    expect(store.paso()).toBe('foto');
    await store.analizarFoto(new Blob(['x']));
    expect(store.paso()).toBe('explorar');
    await store.simularInstruccion('bob rubio', 'voz');
    await store.elegir(store.looks()[0]);
    expect(store.paso()).toBe('decision');
  });

  it('no simula sin foto ni con un pedido vacío', async () => {
    await store.iniciar();
    await expect(store.simularInstruccion('rubio', 'texto')).rejects.toThrow('Primero captura');
    await store.analizarFoto(new Blob(['x']));
    await expect(store.simularInstruccion('   ', 'texto')).rejects.toThrow('Escribe');
  });

  it('guarda el historial con el último look primero y lo muestra', async () => {
    await store.iniciar();
    await store.analizarFoto(new Blob(['x']));
    await store.simularInstruccion('uno', 'texto');
    await store.simularInstruccion('dos', 'texto');
    expect(store.looks().map((l) => l.etiqueta)).toEqual(['dos', 'uno']);
    expect(store.lookActual()?.etiqueta).toBe('dos');
    store.ver(store.looks()[1]);
    expect(store.lookActual()?.etiqueta).toBe('uno');
  });

  it('una foto nueva descarta los looks anteriores', async () => {
    await store.iniciar();
    await store.analizarFoto(new Blob(['x']));
    await store.simularInstruccion('uno', 'texto');
    await store.analizarFoto(new Blob(['y']));
    expect(store.looks()).toEqual([]);
  });

  it('al finalizar envía la satisfacción y limpia todo', async () => {
    await store.iniciar();
    await store.analizarFoto(new Blob(['x']));
    await store.finalizar(9);
    expect(repo.llamadas).toContain('finalizar:9');
    expect(store.activa()).toBe(false);
    expect(store.fotoUrl()).toBeNull();
  });

  it('si el servidor ya cerró la consulta (409) la descarta localmente', async () => {
    await store.iniciar();
    await store.analizarFoto(new Blob(['x']));
    repo.fallarCon = new AppError('La consulta ya terminó', 409);
    await expect(store.simularInstruccion('rubio', 'texto')).rejects.toThrow();
    expect(store.activa()).toBe(false);
  });
});
