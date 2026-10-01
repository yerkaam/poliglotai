import { HttpContextToken, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, finalize, throwError } from 'rxjs';
import { ToastService } from './toast.service';

/** HTTP statuses a request handles on its own screen (e.g. a 429 countdown); no global pop-up for them. */
export const HANDLED_STATUSES = new HttpContextToken<number[]>(() => []);

/** Errors already shown as a pop-up; screens skip them so the learner does not read the same thing twice. */
const reported = new WeakSet<object>();
export function isReported(error: unknown): boolean {
  return typeof error === 'object' && error !== null && reported.has(error);
}

/**
 * No connection: the browser gave up (status 0), or the service worker answered for it — Angular's worker
 * replies with an empty 504 when the network is gone and nothing is cached.
 */
export function isNetworkError(error: unknown): boolean {
  if (!(error instanceof HttpErrorResponse)) return false;
  if (error.status === 0) return true;
  const body = error.error;
  return error.status === 504 && (body === null || body === '' || body instanceof Blob || typeof body === 'string');
}

/** After this long the free Render server is probably waking up: say so instead of a silent spinner. */
const SLOW_MS = 5000;
let pending = 0;
let slowTimer: ReturnType<typeof setTimeout> | undefined;
let slowToast: number | null = null;

/**
 * Problems no single screen can explain: no connection, server errors, too many requests, a slow start.
 * 400/401/403/404 stay with the screens (field errors, the login redirect, "not found").
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toasts = inject(ToastService);
  const handled = req.context.get(HANDLED_STATUSES);

  pending++;
  if (pending === 1) {
    slowTimer = setTimeout(() => {
      slowToast = toasts.info($localize`Сервер оянып жатыр, бірнеше секунд күте тұрыңыз…`, { sticky: true });
    }, SLOW_MS);
  }

  return next(req).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && !handled.includes(error.status)) {
        const message = globalMessage(error);
        if (message) {
          toasts.error(message);
          reported.add(error);
        }
      }
      return throwError(() => error);
    }),
    finalize(() => {
      pending = Math.max(0, pending - 1);
      if (pending === 0) {
        clearTimeout(slowTimer);
        if (slowToast !== null) toasts.dismiss(slowToast);
        slowToast = null;
      }
    }),
  );
};

function globalMessage(error: HttpErrorResponse): string | null {
  if (isNetworkError(error)) {
    // Offline is announced once by NetworkService; this is "online, but the server did not answer".
    return navigator.onLine ? $localize`Серверге қосылу мүмкін болмады. Интернетті тексеріп, қайталаңыз.` : null;
  }
  if (error.status === 429) {
    const wait = Number(error.headers.get('Retry-After') ?? error.error?.retry_after);
    return wait
      ? $localize`Сұраныс тым көп. ${wait}:seconds: секундтан кейін қайталаңыз.`
      : String(error.error?.detail ?? $localize`Сұраныс тым көп. Сәл күтіп, қайталаңыз.`);
  }
  if (error.status >= 500) {
    return typeof error.error?.detail === 'string'
      ? error.error.detail
      : $localize`Серверде қате болды. Бірнеше минуттан кейін қайталап көріңіз.`;
  }
  return null;
}
