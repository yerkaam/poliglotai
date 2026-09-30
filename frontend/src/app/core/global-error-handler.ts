import { ErrorHandler, Injectable, inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { ToastService } from './toast.service';

/** A bug in the page itself: log it and tell the learner, instead of a frozen screen with no word. */
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private toasts = inject(ToastService);

  handleError(error: unknown): void {
    console.error(error);
    // HTTP failures are reported by the interceptor or by the screen that made the request.
    if (error instanceof HttpErrorResponse || (error as { rejection?: unknown })?.rejection instanceof HttpErrorResponse) {
      return;
    }
    this.toasts.error($localize`Бірдеңе дұрыс болмады. Бетті жаңартып көріңіз.`);
  }
}
