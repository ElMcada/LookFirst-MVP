/** Composition root: el único lugar que une cada puerto (application) con su adaptador (infrastructure). */
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { MetricasRepository } from '@analitica/application/indicadores.service';
import { HttpMetricasRepository } from '@analitica/infrastructure/http-metricas.repository';
import { CatalogoRepository } from '@catalogo/application/catalogo.service';
import { HttpCatalogoRepository } from '@catalogo/infrastructure/http-catalogo.repository';
import { Camara, ConsultaRepository, ReconocedorVoz } from '@consulta/application/puertos';
import { HttpConsultaRepository } from '@consulta/infrastructure/http-consulta.repository';
import { WebSpeechVoz } from '@consulta/infrastructure/web-speech.voz';
import { WebRtcCamara } from '@consulta/infrastructure/webrtc.camara';
import { APP_CONFIG } from '@core/config/app-config';
import { authInterceptor } from '@core/http/auth.interceptor';
import { AlmacenSesion, IamRepository } from '@iam/application/iam.repository';
import { HttpIamRepository } from '@iam/infrastructure/http-iam.repository';
import { SessionStorageAlmacen } from '@iam/infrastructure/session-storage.almacen';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor])),
    // La URL del backend puede fijarse al desplegar con window.LOOKFIRST_API_URL (ver index.html)
    { provide: APP_CONFIG, useValue: { apiUrl: (globalThis as { LOOKFIRST_API_URL?: string }).LOOKFIRST_API_URL ?? 'http://localhost:8000' } },

    // IAM
    { provide: IamRepository, useClass: HttpIamRepository },
    { provide: AlmacenSesion, useClass: SessionStorageAlmacen },
    // Catálogo
    { provide: CatalogoRepository, useClass: HttpCatalogoRepository },
    // Consulta
    { provide: ConsultaRepository, useClass: HttpConsultaRepository },
    { provide: Camara, useClass: WebRtcCamara },
    { provide: ReconocedorVoz, useClass: WebSpeechVoz },
    // Analítica
    { provide: MetricasRepository, useClass: HttpMetricasRepository },
  ],
};
