import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';
import { Progress } from './models';

/** Shared progress for the stats bar shown on every screen. Screens call refresh() after a change. */
@Injectable({ providedIn: 'root' })
export class ProgressStore {
  private api = inject(ApiService);
  readonly progress = signal<Progress | null>(null);
  readonly failed = signal(false);

  refresh() {
    // A failure keeps the last numbers on screen; the pop-up (network/server) explains why they are stale.
    this.api.progress().subscribe({
      next: (p) => {
        this.progress.set(p);
        this.failed.set(false);
      },
      error: () => this.failed.set(true),
    });
  }

  clear() {
    this.progress.set(null);
  }
}
