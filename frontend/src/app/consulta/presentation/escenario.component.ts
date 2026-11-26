import { ChangeDetectionStrategy, Component, ElementRef, input, viewChild } from '@angular/core';
import { ComparadorComponent } from './comparador.component';
import { IconComponent } from '@shared/ui/icon.component';

export type ModoEscenario = 'vacio' | 'camara' | 'foto' | 'comparar';

/** Área principal: cámara en vivo, foto analizada o comparación del look. */
@Component({
  selector: 'lf-escenario',
  imports: [ComparadorComponent, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="escenario">
      <video #video [hidden]="modo() !== 'camara'" autoplay playsinline muted></video>
      @if (modo() === 'camara') {
        <div class="guia" aria-hidden="true"><span class="ovalo"></span></div>
        <p class="pista">Centra el rostro dentro del óvalo, de frente y con buena luz</p>
      }
      @if (modo() === 'foto' && fotoUrl()) {
        <img [src]="fotoUrl()" alt="Foto del cliente" />
      }
      @if (modo() === 'comparar' && fotoUrl() && lookUrl()) {
        <lf-comparador [antes]="fotoUrl()!" [despues]="lookUrl()!" />
      }
      @if (modo() === 'vacio') {
        <div class="vacio">
          <lf-icon name="camera" [size]="28" />
          <p>Activa la cámara o sube una foto frontal del cliente</p>
        </div>
      }
      @if (ocupado()) {
        <div class="cargando" role="status">
          <span class="spinner"></span>
          <span>{{ ocupado() }}</span>
        </div>
      }
    </div>
  `,
  styles: `
    .escenario { position: relative; aspect-ratio: 4 / 3; border-radius: var(--radius-lg); overflow: hidden; background: #111013; }
    video, img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    video { transform: scaleX(-1); }
    .guia { position: absolute; inset: 0; display: grid; place-items: center; pointer-events: none;
      background: radial-gradient(ellipse 22% 36% at 50% 47%, transparent 98%, rgb(0 0 0 / .35) 100%); }
    .ovalo { width: 44%; aspect-ratio: 0.82; border: 2px dashed rgb(255 255 255 / .7); border-radius: 50%; transform: translateY(-3%); }
    .pista { position: absolute; left: 50%; bottom: 16px; transform: translateX(-50%); padding: 6px 12px; border-radius: 999px;
      background: rgb(0 0 0 / .55); color: #fff; font-size: 13px; white-space: nowrap; backdrop-filter: blur(6px); }
    .vacio { position: absolute; inset: 0; display: grid; place-content: center; justify-items: center; gap: 12px; color: rgb(255 255 255 / .6); font-size: 14px; text-align: center; padding: 24px; }
    .cargando { position: absolute; inset: 0; display: grid; place-content: center; justify-items: center; gap: 14px;
      background: rgb(17 16 19 / .55); backdrop-filter: blur(3px); color: #fff; font-weight: 550; animation: aparecer .2s var(--ease); }
    .spinner { width: 28px; height: 28px; border-radius: 50%; border: 2.5px solid rgb(255 255 255 / .25); border-top-color: #fff; animation: girar .8s linear infinite; }
    @keyframes girar { to { transform: rotate(360deg); } }
  `,
})
export class EscenarioComponent {
  readonly modo = input.required<ModoEscenario>();
  readonly fotoUrl = input<string | null>(null);
  readonly lookUrl = input<string | null>(null);
  readonly ocupado = input<string | null>(null);
  private readonly videoRef = viewChild.required<ElementRef<HTMLVideoElement>>('video');

  get video(): HTMLVideoElement { return this.videoRef().nativeElement; }
}
