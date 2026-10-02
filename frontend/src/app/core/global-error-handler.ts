import { ErrorHandler, Injectable, inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { MonitoringService } from './monitoring.service';
import { ToastService } from './toast.service';

/** A bug in the page itself: log it and tell the learner, instead of a frozen screen with no word. */
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private toasts = inject(ToastService);
  private monitoring = inject(MonitoringService);

  handleError(error: unknown): void {
    console.error(error);
    // HTTP failures are reported by the interceptor or by the screen that made the request (and the server
    // reports its own errors to monitoring).
    const rejection = (error as { rejection?: unknown })?.rejection;
    if (error instanceof HttpErrorResponse || rejection instanceof HttpErrorResponse) {
      return;
    }
    this.monitoring.report(rejection ?? error);
    this.toasts.error($localize`Бірдеңе дұрыс болмады. Бетті жаңартып көріңіз.`);
  }
}
