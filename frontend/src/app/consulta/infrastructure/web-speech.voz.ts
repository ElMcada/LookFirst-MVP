import { Injectable, signal } from '@angular/core';
import { EventosVoz, ReconocedorVoz } from '@consulta/application/puertos';

// Web Speech API (Chrome/Edge). No tiene tipos oficiales en lib.dom.
interface Reconocimiento {
  lang: string; interimResults: boolean; maxAlternatives: number;
  onresult: ((e: { results: { 0: { 0: { transcript: string } } } }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void; stop(): void;
}
type Ctor = new () => Reconocimiento;
const SR: Ctor | undefined = (globalThis as unknown as { SpeechRecognition?: Ctor; webkitSpeechRecognition?: Ctor }).SpeechRecognition
  ?? (globalThis as unknown as { webkitSpeechRecognition?: Ctor }).webkitSpeechRecognition;

@Injectable()
export class WebSpeechVoz extends ReconocedorVoz {
  private rec: Reconocimiento | null = null;
  readonly soportado = Boolean(SR);
  readonly escuchando = signal(false);

  escuchar(ev: EventosVoz): void {
    if (!SR) return ev.alError('Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge, o escribe el pedido.');
    const rec = new SR();
    Object.assign(rec, { lang: 'es-PE', interimResults: false, maxAlternatives: 1 });
    rec.onresult = (e) => ev.alResultado(e.results[0][0].transcript);
    rec.onerror = (e) => ev.alError(e.error === 'not-allowed'
      ? 'Permite el micrófono para usar comandos de voz.' : 'No te escuché bien. Inténtalo de nuevo.');
    rec.onend = () => { this.rec = null; this.escuchando.set(false); };
    this.rec = rec;
    this.escuchando.set(true);
    rec.start();
  }

  detener(): void { this.rec?.stop(); }
}
