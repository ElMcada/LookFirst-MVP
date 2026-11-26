import { Signal } from '@angular/core';
import { AnalisisRostro, Origen, SimulacionDto } from '@consulta/domain/consulta';

export interface PedidoSimulacion {
  origen: Origen;
  estilo_id?: string;
  instruccion?: string;
}

/** Puerto hacia el backend de consultas. */
export abstract class ConsultaRepository {
  abstract iniciar(version: string): Promise<{ id: string }>;
  abstract subirFoto(id: string, foto: Blob): Promise<AnalisisRostro>;
  abstract simular(id: string, pedido: PedidoSimulacion): Promise<SimulacionDto>;
  abstract elegir(id: string, simulacionId: string): Promise<void>;
  abstract finalizar(id: string, satisfaccion: number | null): Promise<void>;
  abstract revocar(id: string): Promise<void>;
  /** Cierre que sobrevive al cierre de la pestaña (fetch keepalive). */
  abstract finalizarAlSalir(id: string): void;
}

/** Puerto de la cámara del dispositivo (REQ-01). */
export abstract class Camara {
  abstract readonly activa: Signal<boolean>;
  abstract iniciar(video: HTMLVideoElement): Promise<void>;
  abstract capturar(video: HTMLVideoElement): Promise<Blob>;
  abstract detener(): void;
}

export interface EventosVoz {
  alResultado(texto: string): void;
  alError(mensaje: string): void;
}

/** Puerto del reconocimiento de voz (REQ-06). */
export abstract class ReconocedorVoz {
  abstract readonly soportado: boolean;
  abstract readonly escuchando: Signal<boolean>;
  abstract escuchar(eventos: EventosVoz): void;
  abstract detener(): void;
}
