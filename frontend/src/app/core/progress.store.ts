import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';
import { Progress } from './models';
import { ToastService } from './toast.service';

/** Shared progress for the stats bar shown on every screen. Screens call refresh() after a change. */
@Injectable({ providedIn: 'root' })
export class ProgressStore {
  private api = inject(ApiService);
  private toasts = inject(ToastService);
  readonly progress = signal<Progress | null>(null);
  readonly failed = signal(false);

  refresh() {
    // A failure keeps the last numbers on screen; the pop-up (network/server) explains why they are stale.
    this.api.progress().subscribe({
      next: (p) => {
        this.progress.set(p);
        this.failed.set(false);
        this.celebrate(p);
      },
      error: () => this.failed.set(true),
    });
  }

  /** New badges: a congratulation each (or one for a batch, e.g. the first visit after an update), then seen. */
  private celebrate(p: Progress) {
    const fresh = p.new_achievements ?? [];
    if (!fresh.length) return;
    if (fresh.length <= 2) {
      for (const a of fresh) this.toasts.success($localize`🏆 ${a.title_kk}:title: — ${a.description_kk}:text:`);
    } else {
      const titles = fresh.map((a) => a.title_kk).join(', ');
      this.toasts.success($localize`🏆 ${fresh.length}:count: жаңа жетістік: ${titles}:titles:`);
    }
    this.api.achievementsSeen().subscribe({ error: () => undefined });
  }

  clear() {
    this.progress.set(null);
  }
}
