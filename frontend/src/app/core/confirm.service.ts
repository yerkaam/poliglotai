import { Injectable, signal } from '@angular/core';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
}

interface Pending extends ConfirmOptions {
  resolve: (ok: boolean) => void;
}

/** One app-wide confirmation dialog (rendered by ConfirmDialogComponent in the root). */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  readonly pending = signal<Pending | null>(null);
  /** Set right before a navigation the user already confirmed (logout), so leave guards do not ask again. */
  bypassLeaveGuards = false;

  ask(options: ConfirmOptions): Promise<boolean> {
    this.pending()?.resolve(false);
    return new Promise((resolve) => this.pending.set({ ...options, resolve }));
  }

  answer(ok: boolean) {
    const pending = this.pending();
    this.pending.set(null);
    pending?.resolve(ok);
  }
}
