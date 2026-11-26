import { Routes } from '@angular/router';
import { adminGuard, autenticadoGuard, invitadoGuard } from '@iam/presentation/guards';
import { ShellComponent } from './layout/shell.component';

export const routes: Routes = [
  {
    path: 'login', title: 'Iniciar sesión · LookFirst', canActivate: [invitadoGuard],
    loadComponent: () => import('@iam/presentation/login.page').then((m) => m.LoginPage),
  },
  {
    path: '', component: ShellComponent, canActivate: [autenticadoGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'consulta' },
      {
        path: 'consulta', title: 'Consulta · LookFirst',
        loadComponent: () => import('@consulta/presentation/consulta.page').then((m) => m.ConsultaPage),
      },
      {
        path: 'indicadores', title: 'Indicadores · LookFirst',
        loadComponent: () => import('@analitica/presentation/indicadores.page').then((m) => m.IndicadoresPage),
      },
      {
        path: 'catalogo', title: 'Catálogo · LookFirst', canActivate: [adminGuard],
        loadComponent: () => import('@catalogo/presentation/catalogo.page').then((m) => m.CatalogoPage),
      },
      {
        path: 'equipo', title: 'Equipo · LookFirst', canActivate: [adminGuard],
        loadComponent: () => import('@iam/presentation/equipo.page').then((m) => m.EquipoPage),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
