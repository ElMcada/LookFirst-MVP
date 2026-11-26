/** Vocabulario del catálogo. Mismas reglas que el backend (catalogo/domain/estilo.py). */
export type FormaRostro = 'ovalado' | 'redondo' | 'cuadrado' | 'alargado';
export type TipoServicio = 'corte' | 'tinte';
export type TipoCorte = 'conservar' | 'calvo' | 'corto' | 'medio' | 'largo';

export const FORMAS_ROSTRO: FormaRostro[] = ['ovalado', 'redondo', 'cuadrado', 'alargado'];
export const LARGOS_CORTE: Exclude<TipoCorte, 'conservar'>[] = ['calvo', 'corto', 'medio', 'largo'];

export interface Estilo {
  id: string;
  codigo: string;
  nombre: string;
  tipo: TipoServicio;
  descripcion: string;
  prompt_en: string;
  tipo_corte: TipoCorte;
  formas: FormaRostro[];
  color_hex: string | null;
  degradado: boolean;
  activo: boolean;
}

export type DatosEstilo = Omit<Estilo, 'id' | 'activo'>;

export function estiloVacio(): DatosEstilo {
  return { codigo: '', nombre: '', tipo: 'corte', descripcion: '', prompt_en: '', tipo_corte: 'medio', formas: [], color_hex: null, degradado: false };
}

/** Un tinte nunca cambia la silueta; un corte siempre indica el largo resultante. */
export function normalizar(e: DatosEstilo): DatosEstilo {
  const tinte = e.tipo === 'tinte';
  return {
    ...e,
    codigo: e.codigo.trim().toLowerCase(),
    nombre: e.nombre.trim(),
    prompt_en: e.prompt_en.trim(),
    descripcion: e.descripcion.trim(),
    tipo_corte: tinte ? 'conservar' : e.tipo_corte === 'conservar' ? 'medio' : e.tipo_corte,
    color_hex: e.color_hex ? e.color_hex.toUpperCase() : null,
    degradado: tinte && e.degradado,
  };
}

export function validar(e: DatosEstilo): string[] {
  const errores: string[] = [];
  if (!/^[a-z0-9]+(_[a-z0-9]+)*$/.test(e.codigo)) errores.push('El código va en minúsculas con guiones bajos (p. ej. bob_capas).');
  if (e.nombre.length < 2) errores.push('Escribe un nombre.');
  if (e.prompt_en.length < 10) errores.push('El prompt técnico necesita al menos 10 caracteres.');
  if (!e.formas.length) errores.push('Marca al menos una forma de rostro.');
  if (e.tipo === 'tinte' && !e.color_hex) errores.push('Un tinte necesita un color.');
  return errores;
}

export const fondoMuestra = (e: Pick<Estilo, 'color_hex'>): string =>
  e.color_hex ?? 'linear-gradient(135deg, #2b2830, #8a84a3)';
