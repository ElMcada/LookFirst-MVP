import { Estilo, FormaRostro, TipoCorte } from '@catalogo/domain/estilo';

/** Reglas de la consulta en el cliente. Deben coincidir con el backend (consulta/domain/consulta.py). */
export const VERSION_CONSENTIMIENTO = '2026-11-v1';
export const LIMITE_LATENCIA_S = 6; // REQ-04
export const MAX_INSTRUCCION = 300;

export type Origen = 'catalogo' | 'texto' | 'voz';
export type ModoSimulacion = 'ia_generativa' | 'respaldo_local';
export type Paso = 'consentimiento' | 'foto' | 'explorar' | 'decision';

export const PASOS: { id: Paso; texto: string }[] = [
  { id: 'consentimiento', texto: 'Consentimiento' },
  { id: 'foto', texto: 'Foto' },
  { id: 'explorar', texto: 'Explorar looks' },
  { id: 'decision', texto: 'Decisión' },
];

export interface AnalisisRostro {
  forma_rostro: FormaRostro;
  metricas: { alto_ancho: number; mandibula_pomulos: number; frente_pomulos: number };
  razon: string;
  recomendaciones: Estilo[];
}

export interface SimulacionDto {
  id: string;
  etiqueta: string;
  imagen_b64: string;
  latencia_s: number;
  modo: ModoSimulacion;
  tipo_corte: TipoCorte;
  fuente_prompt: string;
  prompt_en: string;
  aviso: string | null;
}

export interface Look {
  id: string;
  etiqueta: string;
  imagenUrl: string;
  latenciaS: number;
  modo: ModoSimulacion;
  origen: Origen;
  promptEn: string;
  aviso: string | null;
}

export function aLook(dto: SimulacionDto, origen: Origen): Look {
  return {
    id: dto.id, etiqueta: dto.etiqueta, imagenUrl: `data:image/jpeg;base64,${dto.imagen_b64}`,
    latenciaS: dto.latencia_s, modo: dto.modo, origen, promptEn: dto.prompt_en, aviso: dto.aviso,
  };
}

export const cumpleLatencia = (l: Look): boolean => l.latenciaS <= LIMITE_LATENCIA_S;

export function pasoActual(estado: { activa: boolean; conFoto: boolean; elegido: boolean }): Paso {
  if (!estado.activa) return 'consentimiento';
  if (!estado.conFoto) return 'foto';
  return estado.elegido ? 'decision' : 'explorar';
}

export function validarInstruccion(texto: string): string | null {
  const t = texto.trim();
  if (!t) return 'Escribe o di qué estilo quieres.';
  if (t.length > MAX_INSTRUCCION) return `Máximo ${MAX_INSTRUCCION} caracteres.`;
  return null;
}
