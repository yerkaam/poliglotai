import { provideHttpClient, withInterceptors, withXsrfConfiguration } from '@angular/common/http';
import { registerLocaleData } from '@angular/common';
import localeKk from '@angular/common/locales/kk';
import {
  ApplicationConfig,
  ErrorHandler,
  LOCALE_ID,
  inject,
  isDevMode,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideRouter, withComponentInputBinding, withInMemoryScrolling } from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth.interceptor';
import { errorInterceptor } from './core/error.interceptor';
import { GlobalErrorHandler } from './core/global-error-handler';
import { AuthService } from './core/auth.service';
import { OfflineQueueService } from './core/offline-queue.service';
import { PwaService } from './core/pwa.service';

registerLocaleData(localeKk);

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding(), withInMemoryScrolling({ scrollPositionRestoration: 'top' })),
    // Django's CSRF cookie is echoed back on every unsafe request.
    provideHttpClient(
      withXsrfConfiguration({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' }),
      // outermost first: the error interceptor sees the final result, after a token refresh and retry
      withInterceptors([errorInterceptor, authInterceptor]),
    ),
    { provide: LOCALE_ID, useValue: 'kk' },
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
    provideAppInitializer(() => inject(AuthService).init()),
    // Installable app, opens without internet; registered once the app has settled (not during start-up).
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
    provideAppInitializer(() => {
      inject(PwaService).init();
      inject(OfflineQueueService).init();
    }),
  ],
};
