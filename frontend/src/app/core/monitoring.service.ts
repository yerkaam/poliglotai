import { Injectable, effect, inject } from '@angular/core';
import { AuthService } from './auth.service';

type Sentry = typeof import('./sentry');

interface ClientConfig {
  sentry_dsn: string;
  environment: string;
  release: string;
}

/** Addresses may carry a reset token or an email: only the path is reported. */
export function withoutQuery(url: string | undefined): string | undefined {
  return url?.split(/[?#]/)[0];
}

/**
 * Error reports (Sentry) for bugs in the page. Off unless the server gives a DSN (SENTRY_FRONTEND_DSN), and then
 * the SDK is loaded as a separate file, so learners on a deploy without monitoring never download it.
 * Reported: the error, the stack, the screen's path and the account id. Not reported: what the learner typed,
 * console output, emails, query strings.
 */
@Injectable({ providedIn: 'root' })
export class MonitoringService {
  private auth = inject(AuthService);
  private sentry: Sentry | null = null;
  private settled = false;
  /** Errors from before the SDK has loaded; sent once it is ready. */
  private early: unknown[] = [];

  constructor() {
    effect(() => {
      const user = this.auth.user();
      this.sentry?.setUser(user ? { id: String(user.id) } : null);
    });
  }

  async init(): Promise<void> {
    try {
      const response = await fetch('/api/config/', { credentials: 'same-origin' });
      if (!response.ok) return;
      const config = (await response.json()) as ClientConfig;
      if (!config.sentry_dsn) return;
      const sentry = await import('./sentry');
      sentry.init({
        dsn: config.sentry_dsn,
        environment: config.environment || undefined,
        release: config.release || undefined,
        dataCollection: { userInfo: false, cookies: false, httpHeaders: false, httpBodies: [], urlQueryParams: false },
        // Angular's ErrorHandler already sees uncaught errors (and reports them here): no second copy from
        // window.onerror. Console breadcrumbs could repeat a learner's text, so they stay off.
        integrations: (defaults) => defaults.filter((i) => i.name !== 'GlobalHandlers' && i.name !== 'Console'),
        beforeBreadcrumb: (crumb) => {
          const data = crumb.data;
          if (data) {
            for (const key of ['url', 'from', 'to']) {
              if (typeof data[key] === 'string') data[key] = withoutQuery(data[key]);
            }
          }
          return crumb;
        },
        beforeSend: (event) => {
          if (event.request) {
            event.request = { url: withoutQuery(event.request.url), headers: event.request.headers };
          }
          return event;
        },
      });
      this.sentry = sentry;
      const user = this.auth.user();
      if (user) sentry.setUser({ id: String(user.id) });
      for (const error of this.early) sentry.captureException(error);
    } catch {
      // No connection or a blocked request: the app works on without reports.
    } finally {
      this.settled = true;
      this.early = [];
    }
  }

  report(error: unknown): void {
    if (this.sentry) {
      this.sentry.captureException(error);
    } else if (!this.settled && this.early.length < 10) {
      this.early.push(error);
    }
  }
}
