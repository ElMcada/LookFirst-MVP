export type Rol = 'admin' | 'estilista';

export interface Usuario {
  id: string;
  nombre: string;
  email: string;
  rol: Rol;
  activo: boolean;
}

export interface Sesion {
  token: string;
  usuario: Usuario;
}

export interface NuevoUsuario {
  nombre: string;
  email: string;
  password: string;
  rol: Rol;
}

export const MIN_PASSWORD = 8;

export const esAdmin = (u: Usuario | null | undefined): boolean => u?.rol === 'admin';

export const etiquetaRol = (rol: Rol): string => (rol === 'admin' ? 'Administrador' : 'Estilista');

export function iniciales(nombre: string): string {
  return nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('');
}

export function validarNuevoUsuario(u: NuevoUsuario): string[] {
  const errores: string[] = [];
  if (u.nombre.trim().length < 2) errores.push('Escribe el nombre completo.');
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(u.email.trim())) errores.push('Correo no válido.');
  if (u.password.length < MIN_PASSWORD) errores.push(`La contraseña necesita al menos ${MIN_PASSWORD} caracteres.`);
  return errores;
}
