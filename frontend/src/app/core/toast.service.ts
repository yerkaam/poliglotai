import { Injectable, signal } from '@angular/core';

export type ToastKind = 'error' | 'success' | 'info';

export interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
  /** Sticky toasts stay until dismissed in code (offline, waking server). */
  sticky: boolean;
}

const DURATION: Record<ToastKind, number> = { error: 7000, success: 3500, info: 5000 };
const MAX_VISIBLE = 3;

/** Small pop-up notifications in the corner. Form field errors stay next to their fields instead. */
@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private nextId = 1;
  private timers = new Map<number, ReturnType<typeof setTimeout>>();

  error(text: string, options?: { sticky?: boolean }) {
    return this.show('error', text, options);
  }
  success(text: string) {
    return this.show('success', text);
  }
  info(text: string, options?: { sticky?: boolean }) {
    return this.show('info', text, options);
  }

  /** The same text is never shown twice at once (ten failing requests → one toast). */
  show(kind: ToastKind, text: string, options: { sticky?: boolean } = {}): number {
    const existing = this.toasts().find((t) => t.kind === kind && t.text === text);
    if (existing) {
      this.schedule(existing);
      return existing.id;
    }
    const toast: Toast = { id: this.nextId++, kind, text, sticky: !!options.sticky };
    this.toasts.update((list) => [...list, toast].slice(-MAX_VISIBLE));
    this.schedule(toast);
    return toast.id;
  }

  dismiss(id: number) {
    clearTimeout(this.timers.get(id));
    this.timers.delete(id);
    this.toasts.update((list) => list.filter((t) => t.id !== id));
  }

  private schedule(toast: Toast) {
    clearTimeout(this.timers.get(toast.id));
    if (!toast.sticky) this.timers.set(toast.id, setTimeout(() => this.dismiss(toast.id), DURATION[toast.kind]));
  }
}
