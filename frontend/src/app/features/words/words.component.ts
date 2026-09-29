import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { INTERVAL_LABELS } from '../../core/labels';
import { Word } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { SpeechService } from '../../core/speech.service';
import { IconComponent } from '../../shared/icon.component';
import { apiErrors } from '../auth/errors';

interface QueueItem {
  word: Word;
  mode: 'review' | 'new';
}

@Component({
  selector: 'app-words',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, RouterLink],
  templateUrl: './words.component.html',
  styleUrl: './words.component.scss',
})
export class WordsComponent implements OnInit {
  private api = inject(ApiService);
  protected speech = inject(SpeechService);
  protected store = inject(ProgressStore);

  protected loading = signal(true);
  protected queue = signal<QueueItem[]>([]);
  protected done = signal(0);
  protected revealed = signal(false);
  protected busy = signal(false);
  protected note = signal('');
  protected error = signal('');
  protected newLimit = signal(0);
  protected newLeft = signal(0);
  protected reviewTotal = signal(0);

  protected intervals = INTERVAL_LABELS;
  protected segments = [1, 2, 3, 4, 5, 6];

  protected current = computed(() => this.queue()[0] ?? null);
  protected total = computed(() => this.done() + this.queue().length);
  protected percent = computed(() => (this.total() ? Math.round((100 * this.done()) / this.total()) : 0));
  protected stageMax = computed(() => Math.max(1, ...(this.store.progress()?.stages.map((s) => s.count) ?? [1])));

  async ngOnInit() {
    await this.load();
  }

  private async load() {
    this.loading.set(true);
    try {
      const today = await firstValueFrom(this.api.today());
      // SRS-06: words due for review come first, then new ones.
      this.queue.set([
        ...today.review.map((word) => ({ word, mode: 'review' as const })),
        ...today.new.map((word) => ({ word, mode: 'new' as const })),
      ]);
      this.reviewTotal.set(today.review.length);
      this.newLimit.set(today.new_limit);
      this.newLeft.set(today.new_left);
      this.done.set(0);
      this.revealed.set(false);
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.loading.set(false);
    }
  }

  protected listen() {
    const item = this.current();
    if (item) this.speech.speak(item.word.word, 0.85);
  }

  protected async answer(answer: 'start' | 'known' | 'remember' | 'forget') {
    const item = this.current();
    if (!item || this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.api.answer(item.word.id, answer));
      const rest = this.queue().slice(1);
      if (answer === 'forget') {
        // SRS-05: one stage down and shown again later in this session.
        this.queue.set([...rest, { word: { ...item.word, stage: res.stage }, mode: 'review' }]);
        this.note.set($localize`Сөз ${res.stage}:stage:-кезеңге оралды, соңында тағы көрсетеміз.`);
      } else {
        this.queue.set(rest);
        this.done.update((d) => d + 1);
        this.note.set(this.noteFor(answer, res.status, res.next_review_date));
      }
      if (answer === 'start') this.newLeft.update((n) => Math.max(0, n - 1));
      this.revealed.set(false);
      this.store.refresh();
    } catch (e) {
      this.error.set(apiErrors(e).general);
      if (answer === 'start') {
        // Limit reached: drop the remaining new words from today's queue.
        this.queue.update((q) => q.filter((i) => i.mode !== 'new'));
      }
    } finally {
      this.busy.set(false);
    }
  }

  private noteFor(answer: string, status: string, next: string | null): string {
    if (answer === 'known') return $localize`Жақсы! Бұл сөзді қайталамаймыз.`;
    if (status === 'learned') return $localize`Керемет! Сөз толық үйренілді.`;
    if (!next) return '';
    const days = Math.round((new Date(next).getTime() - new Date(new Date().toDateString()).getTime()) / 86400000);
    return $localize`Келесі қайталау ${days}:days: күннен кейін`;
  }
}
