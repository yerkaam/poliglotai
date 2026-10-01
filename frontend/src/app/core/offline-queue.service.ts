import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { isNetworkError } from './error.interceptor';
import { ProgressStore } from './progress.store';
import { ReviewQuiz } from './models';
import { ToastService } from './toast.service';

const KEY = 'poliglot-offline-answers';

export type QueuedAnswer =
  | { kind: 'check'; wordId: number; mode: ReviewQuiz['mode']; answer: string }
  | { kind: 'answer'; wordId: number; answer: 'start' | 'known' };

/**
 * Card answers given without internet. They are kept on the device and sent, in order, once the connection
 * is back; the server checks each one again, so the stages end up exactly as if the learner had been online.
 */
@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private api = inject(ApiService);
  private store = inject(ProgressStore);
  private toasts = inject(ToastService);
  private flushing = false;

  readonly pending = signal<QueuedAnswer[]>(read());

  init() {
    if (typeof window === 'undefined') return;
    window.addEventListener('online', () => this.flush());
    this.flush();
  }

  add(item: QueuedAnswer) {
    this.pending.update((list) => [...list, item]);
    write(this.pending());
  }

  /** Word ids answered offline today: they are not shown again from a cached list. */
  pendingWordIds(): Set<number> {
    return new Set(this.pending().map((item) => item.wordId));
  }

  async flush() {
    if (this.flushing || !this.pending().length || (typeof navigator !== 'undefined' && !navigator.onLine)) return;
    this.flushing = true;
    let sent = 0;
    try {
      while (this.pending().length) {
        const item = this.pending()[0];
        try {
          if (item.kind === 'check') await firstValueFrom(this.api.checkReview(item.wordId, item.mode, item.answer));
          else await firstValueFrom(this.api.answer(item.wordId, item.answer));
          sent++;
        } catch (e) {
          // No connection after all: keep the rest for the next try. Anything else (already answered, limit
          // reached) the server has decided: drop it and go on.
          if (isNetworkError(e) || (e instanceof HttpErrorResponse && e.status >= 500)) break;
        }
        this.pending.update((list) => list.slice(1));
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
