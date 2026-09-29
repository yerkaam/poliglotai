import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';
import { Progress } from './models';

/** Shared progress for the stats bar shown on every screen. Screens call refresh() after a change. */
@Injectable({ providedIn: 'root' })
export class ProgressStore {
  private api = inject(ApiService);
  readonly progress = signal<Progress | null>(null);

  refresh() {
    this.api.progress().subscribe({ next: (p) => this.progress.set(p), error: () => undefined });
  }

  clear() {
    this.progress.set(null);
  }
}
