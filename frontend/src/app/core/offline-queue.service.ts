import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, effect, inject, signal, untracked } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { isNetworkError } from './error.interceptor';
import { ProgressStore } from './progress.store';
import { ReviewQuiz } from './models';
import { ToastService } from './toast.service';

const KEY = 'poliglot-offline-answers';

export type QueuedAnswer = (
  | { kind: 'check'; wordId: number; mode: ReviewQuiz['mode']; answer: string }
  | { kind: 'answer'; wordId: number; answer: 'start' | 'known' }
) & {
  /** Whose answer it is: on a shared phone it must never reach the next learner's account. */
  userId?: number;
};

/**
 * Card answers given without internet. They are kept on the device and sent, in order, once the connection
 * is back; the server checks each one again, so the stages end up exactly as if the learner had been online.
 */
@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private api = inject(ApiService);
  private store = inject(ProgressStore);
  private toasts = inject(ToastService);
  private auth = inject(AuthService);
  private flushing = false;

  readonly pending = signal<QueuedAnswer[]>(read());

  constructor() {
    // Sent once someone is logged in (start-up, or a login later): only that learner's own answers.
    effect(() => {
      if (this.auth.user()) untracked(() => void this.flush());
    });
  }

  init() {
    if (typeof window === 'undefined') return;
    window.addEventListener('online', () => this.flush());
  }

  add(item: QueuedAnswer) {
    this.pending.update((list) => [...list, { ...item, userId: this.auth.user()?.id }]);
    write(this.pending());
  }

  /** Word ids this learner answered offline: they are not shown again from a cached list. */
  pendingWordIds(): Set<number> {
    return new Set(this.mine().map((item) => item.wordId));
  }

  private mine(): QueuedAnswer[] {
    const id = this.auth.user()?.id;
    return id === undefined ? [] : this.pending().filter((item) => item.userId === undefined || item.userId === id);
  }

  async flush() {
    if (this.flushing || !this.mine().length || (typeof navigator !== 'undefined' && !navigator.onLine)) return;
    this.flushing = true;
    let sent = 0;
    try {
      for (let item = this.mine()[0]; item; item = this.mine()[0]) {
        try {
          if (item.kind === 'check') await firstValueFrom(this.api.checkReview(item.wordId, item.mode, item.answer));
          else await firstValueFrom(this.api.answer(item.wordId, item.answer));
          sent++;
        } catch (e) {
          // No connection after all, or the session ended: keep the rest for the next try. Anything else
          // (already answered, limit reached, the card changed meanwhile) the server has decided: drop it.
          const status = e instanceof HttpErrorResponse ? e.status : 0;
          if (isNetworkError(e) || status === 401 || status === 403 || status >= 500) break;
        }
        const done = item;
        this.pending.update((list) => list.filter((i) => i !== done));
        write(this.pending());
      }
    } finally {
      this.flushing = false;
    }
    if (sent) {
      this.toasts.success($localize`Интернетсіз берілген ${sent}:count: жауап сақталды.`);
      this.store.refresh();
    }
  }
}

function read(): QueuedAnswer[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]');
  } catch {
    return [];
  }
}

function write(list: QueuedAnswer[]) {
  try {
    if (list.length) localStorage.setItem(KEY, JSON.stringify(list));
    else localStorage.removeItem(KEY);
  } catch {
    /* storage may be blocked */
  }
}
