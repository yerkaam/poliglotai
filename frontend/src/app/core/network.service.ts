import { Injectable, inject, signal } from '@angular/core';
import { ToastService } from './toast.service';

/** Announces a lost connection once (sticky) and its return. */
@Injectable({ providedIn: 'root' })
export class NetworkService {
  private toasts = inject(ToastService);
  readonly online = signal(typeof navigator === 'undefined' || navigator.onLine);
  private offlineToast: number | null = null;

  constructor() {
    if (typeof window === 'undefined') return;
    window.addEventListener('offline', () => this.update(false));
    window.addEventListener('online', () => this.update(true));
    if (!navigator.onLine) this.update(false);
  }

  private update(online: boolean) {
    this.online.set(online);
    if (!online) {
      this.offlineToast = this.toasts.error($localize`Интернет жоқ. Байланыс қалпына келгенде жалғастырамыз.`, {
        sticky: true,
      });
    } else if (this.offlineToast !== null) {
      this.toasts.dismiss(this.offlineToast);
      this.offlineToast = null;
      this.toasts.success($localize`Байланыс қалпына келді.`);
    }
  }
}
