import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, catchError, finalize, shareReplay, switchMap, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { ConfirmService } from './confirm.service';

const NO_REFRESH = ['/api/auth/login/', '/api/auth/register/', '/api/auth/refresh/', '/api/auth/logout/', '/api/auth/csrf/'];

let refreshing$: Observable<unknown> | null = null;

/** The access token lives 15 minutes. On a 401 the interceptor refreshes it once and retries. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const api = inject(ApiService);
  const auth = inject(AuthService);
  const confirm = inject(ConfirmService);

  return next(req).pipe(
    catchError((error: unknown) => {
      const canRefresh =
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !NO_REFRESH.some((url) => req.url.startsWith(url));
      if (!canRefresh) return throwError(() => error);

      refreshing$ ??= api.refresh().pipe(
        shareReplay(1),
        finalize(() => (refreshing$ = null)),
      );
      return refreshing$.pipe(
        switchMap(() => next(req)),
        catchError((refreshError: unknown) => {
          if (auth.isLoggedIn()) {
            // The session is gone: nothing on the page can be saved, so leave without asking.
            confirm.bypassLeaveGuards = true;
            auth.clear().finally(() => (confirm.bypassLeaveGuards = false));
          }
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
