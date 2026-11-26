import { Injectable, signal } from '@angular/core';
import { AppError } from '@core/errors/app-error';
import { Camara } from '@consulta/application/puertos';

@Injectable()
export class WebRtcCamara extends Camara {
  private stream: MediaStream | null = null;
  private video: HTMLVideoElement | null = null;
  readonly activa = signal(false);

  async iniciar(video: HTMLVideoElement): Promise<void> {
    if (!this.stream) {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false,
        });
      } catch {
        throw new AppError('No se pudo acceder a la cámara. Revisa los permisos del navegador o sube una foto.');
      }
    }
    this.video = video;
    video.srcObject = this.stream;
    this.activa.set(true);
  }

  capturar(video: HTMLVideoElement): Promise<Blob> {
    const c = document.createElement('canvas');
    c.width = video.videoWidth;
    c.height = video.videoHeight;
    c.getContext('2d')!.drawImage(video, 0, 0);
    return new Promise((ok, mal) => c.toBlob((b) => (b ? ok(b) : mal(new AppError('No se pudo capturar la foto.'))), 'image/jpeg', 0.92));
  }

  detener(): void {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
    if (this.video) this.video.srcObject = null;
    this.video = null;
    this.activa.set(false);
  }
}
