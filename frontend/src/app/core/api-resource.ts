import { signal } from '@angular/core';
import { Observable } from 'rxjs';

/**
 * Data a screen loads once, with loading and error states and a retry.
 * (toSignal() on a failing request re-throws on every read and breaks the whole screen.)
 */
export function apiResource<T>(fetch: () => Observable<T>, initial: T) {
  const value = signal<T>(initial);
  const loading = signal(true);
  const failed = signal(false);

  const reload = () => {
    loading.set(true);
    failed.set(false);
    fetch().subscribe({
      next: (v) => value.set(v),
      error: () => {
        failed.set(true);
        loading.set(false);
      },
      complete: () => loading.set(false),
    });
  };
  reload();

  return { value: value.asReadonly(), loading: loading.asReadonly(), failed: failed.asReadonly(), reload };
}
