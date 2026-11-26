import { ChangeDetectionStrategy, Component, computed, HostListener, inject, OnDestroy, signal, viewChild } from '@angular/core';
import { mensajeDe } from '@core/errors/app-error';
import { Estilo } from '@catalogo/domain/estilo';
import { EstiloItemComponent } from '@catalogo/presentation/estilo-item.component';
import { ConsultaStore } from '@consulta/application/consulta.store';
import { Camara } from '@consulta/application/puertos';
import { cumpleLatencia, LIMITE_LATENCIA_S, Look } from '@consulta/domain/consulta';
import { ConfirmacionDialog } from '@shared/ui/confirmacion.dialog';
import { IconComponent } from '@shared/ui/icon.component';
import { ToastService } from '@shared/ui/toast.service';
import { CierreDialog } from './cierre.dialog';
import { ConsentimientoDialog } from './consentimiento.dialog';
import { EscenarioComponent, ModoEscenario } from './escenario.component';
import { HistorialComponent } from './historial.component';
import { Pedido, SolicitudComponent } from './solicitud.component';
import { StepperComponent } from './stepper.component';

const ORIGEN_TEXTO = { catalogo: 'Del catálogo', texto: 'Pedido escrito', voz: 'Pedido por voz' } as const;

@Component({
  selector: 'lf-consulta-page',
  imports: [
    IconComponent, StepperComponent, EscenarioComponent, HistorialComponent, SolicitudComponent, EstiloItemComponent,
    ConsentimientoDialog, CierreDialog, ConfirmacionDialog,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './consulta.page.html',
  styleUrl: './consulta.page.scss',
})
export class ConsultaPage implements OnDestroy {
  protected readonly store = inject(ConsultaStore);
  protected readonly camara = inject(Camara);
  private readonly toast = inject(ToastService);

  private readonly escenario = viewChild.required(EscenarioComponent);
  private readonly consentimiento = viewChild.required(ConsentimientoDialog);
  private readonly cierre = viewChild.required(CierreDialog);
  private readonly confirmacion = viewChild.required(ConfirmacionDialog);

  /** El estilista pidió volver a la cámara (aunque ya haya un look en pantalla). */
  protected readonly verCamara = signal(false);
  protected readonly libre = computed(() => !this.store.ocupado());
  protected readonly modo = computed<ModoEscenario>(() => {
    if (this.verCamara() && this.camara.activa()) return 'camara';
    if (this.store.lookActual()) return 'comparar';
    if (this.store.fotoUrl()) return 'foto';
    return 'vacio';
  });
  protected readonly limite = LIMITE_LATENCIA_S;
  protected readonly cumpleLatencia = cumpleLatencia;
  protected readonly origenTexto = ORIGEN_TEXTO;

  @HostListener('window:pagehide')
  alSalir() { this.store.cerrarAlSalir(); this.camara.detener(); }

  /** Al ir a otra sección se apaga la cámara; la consulta (y sus looks) sigue abierta. */
  ngOnDestroy() { this.apagar(); }

  async iniciar() {
    if (!(await this.consentimiento().pedir())) {
      this.toast.info('Sin el consentimiento del cliente la cámara permanece bloqueada.');
      return;
    }
    if (await this.ejecutar(() => this.store.iniciar())) await this.abrirCamara();
  }

  async abrirCamara() {
    this.verCamara.set(true);
    try {
      await this.camara.iniciar(this.escenario().video);
    } catch (e) {
      this.verCamara.set(false);
      this.toast.error(mensajeDe(e));
    }
  }

  async capturar() {
    try {
      await this.analizar(await this.camara.capturar(this.escenario().video));
    } catch (e) {
      this.toast.error(mensajeDe(e));
    }
  }

  subir(ev: Event) {
    const input = ev.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    if (archivo) this.analizar(archivo);
  }

  private async analizar(foto: Blob) {
    if (await this.ejecutar(() => this.store.analizarFoto(foto))) {
      this.camara.detener();
      this.verCamara.set(false);
    }
  }

  simularEstilo(e: Estilo) { this.ejecutar(() => this.store.simularEstilo(e)); }
  simularPedido(p: Pedido) { this.ejecutar(() => this.store.simularInstruccion(p.texto, p.origen)); }
  ver(l: Look) { this.verCamara.set(false); this.store.ver(l); }

  async elegir(l: Look) {
    if (await this.ejecutar(() => this.store.elegir(l))) this.toast.ok(`Elegido: ${l.etiqueta}. Puedes finalizar cuando quieras.`);
  }

  async finalizar() {
    const r = await this.cierre().pedir(this.store.elegidoId() !== null);
    if (!r) return;
    if (await this.ejecutar(() => this.store.finalizar(r.satisfaccion))) {
      this.apagar();
      this.toast.ok('Consulta finalizada. La foto se eliminó del servidor.');
    }
  }

  async revocar() {
    const ok = await this.confirmacion().pedir({
      titulo: '¿El cliente retira su consentimiento?',
      texto: 'Se eliminarán de inmediato su foto y todas las simulaciones de esta consulta.',
      confirmar: 'Retirar y eliminar', peligro: true,
    });
    if (ok && (await this.ejecutar(() => this.store.revocar()))) {
      this.apagar();
      this.toast.ok('Consentimiento retirado. Se eliminaron la foto y las simulaciones.');
    }
  }

  private apagar() {
    this.camara.detener();
    this.verCamara.set(false);
  }

  /** Ejecuta un caso de uso y muestra el error si falla. Devuelve si tuvo éxito. */
  private async ejecutar(fn: () => Promise<void>): Promise<boolean> {
    try {
      await fn();
      if (!this.store.activa()) this.apagar();
      return true;
    } catch (e) {
      if (!this.store.activa()) this.apagar();
      this.toast.error(mensajeDe(e));
      return false;
    }
  }
}
