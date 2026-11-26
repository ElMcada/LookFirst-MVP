import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { mensajeDe } from '@core/errors/app-error';
import { CatalogoService } from '@catalogo/application/catalogo.service';
import { DatosEstilo, Estilo, estiloVacio, fondoMuestra, FORMAS_ROSTRO, FormaRostro, LARGOS_CORTE } from '@catalogo/domain/estilo';
import { IconComponent } from '@shared/ui/icon.component';
import { ToastService } from '@shared/ui/toast.service';

type Filtro = 'todos' | 'corte' | 'tinte';

@Component({
  selector: 'lf-catalogo-page',
  imports: [FormsModule, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <header class="page-head">
        <div>
          <p class="eyebrow">Administración</p>
          <h1>Catálogo del salón</h1>
          <p class="muted">Solo se recomiendan y simulan los servicios activos de esta lista.</p>
        </div>
        <button class="btn btn-primary" (click)="nuevo()"><lf-icon name="plus" /> Nuevo estilo</button>
      </header>

      <div class="grid">
        <section class="card lista">
          <div class="filtros" role="tablist">
            @for (f of filtros; track f.valor) {
              <button class="seg" role="tab" [attr.aria-selected]="filtro() === f.valor" (click)="filtro.set(f.valor)">{{ f.texto }}</button>
            }
            <span class="spacer"></span>
            <span class="subtle">{{ visibles().length }} estilos</span>
          </div>
          <table class="table">
            <thead><tr><th>Estilo</th><th>Resultado</th><th>Recomendado para</th><th></th></tr></thead>
            <tbody>
              @for (e of visibles(); track e.id) {
                <tr [class.inactive]="!e.activo" [class.sel]="editandoId() === e.id">
                  <td>
                    <div class="estilo">
                      <span class="swatch" [style.background]="fondoMuestra(e)"></span>
                      <div><strong>{{ e.nombre }}</strong><div class="subtle">{{ e.codigo }}</div></div>
                    </div>
                  </td>
                  <td><span class="badge">{{ e.tipo === 'tinte' ? 'Tinte' : 'Corte ' + e.tipo_corte }}</span></td>
                  <td class="formas">{{ e.formas.join(', ') }}</td>
                  <td><div class="acciones">
                      <button class="btn btn-ghost btn-sm" (click)="editar(e)"><lf-icon name="edit" [size]="15" /> Editar</button>
                      <button class="btn btn-ghost btn-sm" (click)="alternar(e)">{{ e.activo ? 'Desactivar' : 'Activar' }}</button>
                    </div></td>
                </tr>
              }
            </tbody>
          </table>
        </section>

        <form class="card card-pad stack editor" (ngSubmit)="guardar()">
          <div class="row">
            <h2>{{ editandoId() ? 'Editar estilo' : 'Nuevo estilo' }}</h2>
            <span class="spacer"></span>
            @if (editandoId()) { <button type="button" class="btn btn-ghost btn-sm" (click)="nuevo()">Cancelar</button> }
          </div>

          <div class="seg-group" role="radiogroup" aria-label="Tipo de servicio">
            <button type="button" class="seg" [attr.aria-selected]="datos.tipo === 'corte'" (click)="datos.tipo = 'corte'"><lf-icon name="scissors" [size]="16" /> Corte</button>
            <button type="button" class="seg" [attr.aria-selected]="datos.tipo === 'tinte'" (click)="datos.tipo = 'tinte'"><lf-icon name="sparkles" [size]="16" /> Tinte</button>
          </div>

          <div class="dos">
            <label class="field">Nombre<input class="input" name="nombre" [(ngModel)]="datos.nombre" required /></label>
            <label class="field">Código<input class="input" name="codigo" [(ngModel)]="datos.codigo" placeholder="bob_capas" required /></label>
          </div>

          @if (datos.tipo === 'corte') {
            <label class="field">Largo resultante
              <select class="select" name="largo" [(ngModel)]="datos.tipo_corte">
                @for (l of largos; track l) { <option [value]="l">{{ l }}</option> }
              </select>
            </label>
          }

          <div class="field">Color
            <div class="color">
              <label class="check"><input type="checkbox" name="usaColor" [ngModel]="!!datos.color_hex" (ngModelChange)="datos.color_hex = $event ? '#5A3A28' : null" /> {{ datos.tipo === 'tinte' ? 'Color del tinte' : 'Cambiar también el color' }}</label>
              @if (datos.color_hex) {
                <input type="color" name="color" [(ngModel)]="datos.color_hex" aria-label="Color" />
                <code>{{ datos.color_hex.toUpperCase() }}</code>
              }
            </div>
            @if (datos.tipo === 'tinte') {
              <label class="check"><input type="checkbox" name="degradado" [(ngModel)]="datos.degradado" /> Degradado (balayage / ombré)</label>
            }
          </div>

          <fieldset class="field">
            <legend>Recomendado para rostro</legend>
            <div class="chips">
              @for (f of formas; track f) {
                <button type="button" class="chip" [attr.aria-pressed]="datos.formas.includes(f)" (click)="alternarForma(f)">{{ f }}</button>
              }
            </div>
          </fieldset>

          <label class="field">Descripción para el cliente<textarea class="textarea" name="descripcion" rows="2" [(ngModel)]="datos.descripcion"></textarea></label>
          <label class="field">Prompt técnico (inglés)
            <textarea class="textarea" name="prompt" rows="3" [(ngModel)]="datos.prompt_en" placeholder="layered bob haircut at jaw length, soft layers" required></textarea>
            <span class="subtle">Describe solo el cabello; la calidad fotográfica la añade el sistema.</span>
          </label>

          <button class="btn btn-primary" [disabled]="guardando()">{{ editandoId() ? 'Guardar cambios' : 'Crear estilo' }}</button>
        </form>
      </div>
    </div>
  `,
  styles: `
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 20px; align-items: start; }
    .lista { padding: 8px 8px 4px; overflow-x: auto; }
    .filtros { display: flex; align-items: center; gap: 4px; padding: 8px 8px 16px; }
    .seg { height: 32px; padding: 0 12px; border: 0; border-radius: var(--radius-sm); background: none; color: var(--text-2); font-size: 13px; font-weight: 550; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
    .seg:hover { background: var(--surface-2); color: var(--text); }
    .seg[aria-selected="true"] { background: var(--surface-2); color: var(--text); box-shadow: inset 0 0 0 1px var(--border); }
    .seg-group { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 4px; background: var(--surface-2); border-radius: var(--radius-sm); }
    .seg-group .seg { justify-content: center; }
    .seg-group .seg[aria-selected="true"] { background: var(--surface); box-shadow: var(--shadow-sm), inset 0 0 0 1px var(--border); }
    .estilo { display: flex; gap: 12px; align-items: center; }
    .formas { color: var(--text-2); text-transform: capitalize; }
    .acciones { display: flex; justify-content: flex-end; gap: 4px; }
    tr.sel td { background: var(--accent-soft); }
    .editor { position: sticky; top: 84px; }
    .dos { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .color { display: flex; align-items: center; gap: 12px; min-height: 40px; }
    .color input[type="color"] { width: 40px; height: 32px; border: 1px solid var(--border); border-radius: 6px; padding: 2px; background: none; }
    .color code { font-size: 12px; color: var(--text-2); }
    fieldset { border: 0; padding: 0; margin: 0; } legend { padding: 0; margin-bottom: 6px; }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; }
    .chip { height: 32px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--border); background: var(--surface); font-size: 13px; text-transform: capitalize; cursor: pointer; color: var(--text-2); }
    .chip[aria-pressed="true"] { background: var(--text); border-color: var(--text); color: #fff; }
    @media (max-width: 1060px) { .grid { grid-template-columns: 1fr; } .editor { position: static; } }
  `,
})
export class CatalogoPage implements OnInit {
  private readonly catalogo = inject(CatalogoService);
  private readonly toast = inject(ToastService);
  protected readonly estilos = signal<Estilo[]>([]);
  protected readonly filtro = signal<Filtro>('todos');
  protected readonly editandoId = signal<string | null>(null);
  protected readonly guardando = signal(false);
  protected datos: DatosEstilo = estiloVacio();
  protected readonly formas = FORMAS_ROSTRO;
  protected readonly largos = LARGOS_CORTE;
  protected readonly fondoMuestra = fondoMuestra;
  protected readonly filtros: { valor: Filtro; texto: string }[] = [
    { valor: 'todos', texto: 'Todos' }, { valor: 'corte', texto: 'Cortes' }, { valor: 'tinte', texto: 'Tintes' },
  ];
  protected readonly visibles = computed(() =>
    this.estilos().filter((e) => this.filtro() === 'todos' || e.tipo === this.filtro()));

  ngOnInit() { this.cargar(); }

  async cargar() {
    try { this.estilos.set(await this.catalogo.listar(true)); } catch (e) { this.toast.error(mensajeDe(e)); }
  }

  nuevo() {
    this.editandoId.set(null);
    this.datos = estiloVacio();
  }

  editar(e: Estilo) {
    this.editandoId.set(e.id);
    const { id: _id, activo: _activo, ...datos } = e;
    this.datos = { ...datos, formas: [...e.formas] };
  }

  alternarForma(f: FormaRostro) {
    const s = new Set(this.datos.formas);
    if (s.has(f)) s.delete(f); else s.add(f);
    this.datos.formas = FORMAS_ROSTRO.filter((x) => s.has(x));
  }

  async guardar() {
    this.guardando.set(true);
    try {
      const e = await this.catalogo.guardar(this.datos, this.editandoId());
      this.toast.ok(`«${e.nombre}» guardado.`);
      this.nuevo();
      await this.cargar();
    } catch (e) {
      this.toast.error(mensajeDe(e));
    } finally {
      this.guardando.set(false);
    }
  }

  async alternar(e: Estilo) {
    try { await this.catalogo.cambiarEstado(e, !e.activo); await this.cargar(); } catch (err) { this.toast.error(mensajeDe(err)); }
  }
}
