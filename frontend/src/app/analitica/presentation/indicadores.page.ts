import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { mensajeDe } from '@core/errors/app-error';
import { Indicadores, IndicadoresService } from '@analitica/application/indicadores.service';
import { rangoPorDefecto } from '@analitica/domain/indicadores';
import { EquipoService } from '@iam/application/equipo.service';
import { SesionStore } from '@iam/application/sesion.store';
import { Usuario } from '@iam/domain/usuario';
import { IconComponent } from '@shared/ui/icon.component';
import { ToastService } from '@shared/ui/toast.service';

@Component({
  selector: 'lf-indicadores-page',
  imports: [FormsModule, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <header class="page-head">
        <div>
          <p class="eyebrow">Analítica</p>
          <h1>Indicadores</h1>
          <p class="muted">{{ esAdmin() ? 'Resultados del salón frente a las metas del proyecto.' : 'Tus consultas frente a las metas del proyecto.' }}</p>
        </div>
        <form class="filtros" (ngSubmit)="cargar()">
          <label class="field">Desde<input class="input" type="date" name="desde" [(ngModel)]="desde" /></label>
          <label class="field">Hasta<input class="input" type="date" name="hasta" [(ngModel)]="hasta" /></label>
          @if (esAdmin()) {
            <label class="field">Estilista
              <select class="select" name="estilista" [(ngModel)]="estilistaId">
                <option [ngValue]="null">Todo el salón</option>
                @for (u of estilistas(); track u.id) { <option [ngValue]="u.id">{{ u.nombre }}</option> }
              </select>
            </label>
          }
          <button class="btn btn-secondary" [disabled]="cargando()"><lf-icon name="refresh" [size]="16" /> Actualizar</button>
        </form>
      </header>

      @if (datos(); as d) {
        <div class="kpis">
          @for (k of d.kpis; track k.titulo) {
            <article class="card kpi">
              <div class="kpi-top">
                <h3>{{ k.titulo }}</h3>
                @if (k.cumple !== null) {
                  <span class="badge" [class.ok]="k.cumple" [class.warn]="!k.cumple"><span class="dot"></span>{{ k.cumple ? 'Cumple' : 'No cumple' }}</span>
                }
              </div>
              <p class="valor">{{ k.valor }}<span>{{ k.unidad }}</span></p>
              <p class="meta">{{ k.meta }}</p>
              <p class="subtle">{{ k.detalle }}</p>
            </article>
          }
        </div>

        <div class="detalle">
          <section class="card card-pad">
            <h2>Cómo piden los looks</h2>
            <p class="subtle">{{ d.simulaciones }} simulaciones · {{ d.promedioLooks ?? '—' }} por consulta</p>
            <div class="barras">
              @for (b of d.origenes; track b.etiqueta) {
                <div class="barra"><div class="barra-txt"><span>{{ b.etiqueta }}</span><span class="subtle">{{ b.valor }} · {{ b.porcentaje }} %</span></div>
                  <div class="pista"><span [style.width.%]="b.porcentaje"></span></div></div>
              } @empty { <p class="muted">Sin simulaciones en el periodo.</p> }
            </div>
          </section>
          <section class="card card-pad">
            <h2>Motor utilizado</h2>
            <p class="subtle">IA generativa requiere Colab activo</p>
            <div class="barras">
              @for (b of d.modos; track b.etiqueta) {
                <div class="barra"><div class="barra-txt"><span>{{ b.etiqueta }}</span><span class="subtle">{{ b.valor }} · {{ b.porcentaje }} %</span></div>
                  <div class="pista"><span [style.width.%]="b.porcentaje"></span></div></div>
              } @empty { <p class="muted">Sin simulaciones en el periodo.</p> }
            </div>
          </section>
          <section class="card card-pad">
            <h2>Looks más elegidos</h2>
            <p class="subtle">Decisiones finales de los clientes</p>
            <ol class="top">
              @for (t of d.topLooks; track t.nombre; let i = $index) {
                <li><span class="pos">{{ i + 1 }}</span><span class="spacer">{{ t.nombre }}</span><strong>{{ t.veces }}</strong></li>
              } @empty { <li class="muted">Aún no hay looks elegidos.</li> }
            </ol>
          </section>
        </div>
      } @else {
        <div class="kpis">@for (i of [1, 2, 3, 4]; track i) { <div class="card kpi esqueleto"></div> }</div>
      }
    </div>
  `,
  styles: `
    .filtros { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px; }
    .filtros .input, .filtros .select { width: auto; }
    .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
    .kpi { padding: 20px; display: grid; gap: 4px; align-content: start; min-height: 168px; }
    .kpi-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
    .kpi h3 { color: var(--text-2); font-weight: 550; }
    .valor { font-size: 34px; font-weight: 650; letter-spacing: -0.03em; margin-top: 8px; font-variant-numeric: tabular-nums; }
    .valor span { font-size: 15px; font-weight: 500; color: var(--text-3); margin-left: 4px; letter-spacing: 0; }
    .meta { font-size: 13px; font-weight: 550; }
    .detalle { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 16px; }
    .barras { display: grid; gap: 14px; margin-top: 18px; }
    .barra-txt { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px; }
    .pista { height: 6px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
    .pista span { display: block; height: 100%; border-radius: 999px; background: var(--text); }
    .top { list-style: none; padding: 0; margin: 14px 0 0; }
    .top li { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid var(--border); font-size: 14px; }
    .top li:first-child { border-top: 0; }
    .pos { width: 22px; height: 22px; border-radius: 50%; background: var(--surface-2); display: grid; place-items: center; font-size: 12px; font-weight: 600; }
    .esqueleto { background: linear-gradient(90deg, var(--surface), var(--surface-2), var(--surface)); background-size: 200% 100%; animation: brillo 1.6s infinite; }
    @keyframes brillo { to { background-position: -200% 0; } }
    @media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .detalle { grid-template-columns: 1fr; } }
    @media (max-width: 560px) { .kpis { grid-template-columns: 1fr; } }
  `,
})
export class IndicadoresPage implements OnInit {
  private readonly servicio = inject(IndicadoresService);
  private readonly equipo = inject(EquipoService);
  private readonly toast = inject(ToastService);
  protected readonly esAdmin = inject(SesionStore).esAdmin;
  protected readonly datos = signal<Indicadores | null>(null);
  protected readonly estilistas = signal<Usuario[]>([]);
  protected readonly cargando = signal(false);
  protected desde = rangoPorDefecto().desde;
  protected hasta = rangoPorDefecto().hasta;
  protected estilistaId: string | null = null;

  async ngOnInit() {
    if (this.esAdmin()) {
      this.equipo.listar().then((u) => this.estilistas.set(u.filter((x) => x.rol === 'estilista'))).catch(() => {});
    }
    await this.cargar();
  }

  async cargar() {
    this.cargando.set(true);
    try {
      this.datos.set(await this.servicio.obtener({ desde: this.desde, hasta: this.hasta, estilistaId: this.estilistaId }));
    } catch (e) {
      this.toast.error(mensajeDe(e));
    } finally {
      this.cargando.set(false);
    }
  }
}
