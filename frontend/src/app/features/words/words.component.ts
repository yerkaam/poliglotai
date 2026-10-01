import { HttpErrorResponse } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { INTERVAL_LABELS } from '../../core/labels';
import { ReviewCheck, Word } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { SpeechService } from '../../core/speech.service';
import { IconComponent } from '../../shared/icon.component';
import { LoadErrorComponent } from '../../shared/load-error.component';
import { MicButtonComponent } from '../../shared/mic-button.component';
import { apiErrors } from '../auth/errors';

interface QueueItem {
  word: Word;
  mode: 'review' | 'new';
}

@Component({
  selector: 'app-words',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, RouterLink, LoadErrorComponent, MicButtonComponent],
  templateUrl: './words.component.html',
  styleUrl: './words.component.scss',
})
export class WordsComponent implements OnInit {
  private api = inject(ApiService);
  protected speech = inject(SpeechService);
  protected store = inject(ProgressStore);

  protected loading = signal(true);
  /** Today's cards could not be loaded: the screen offers a retry instead of "all done". */
  protected loadFailed = signal(false);
  protected queue = signal<QueueItem[]>([]);
  protected done = signal(0);
  /** The verdict on the review card on screen; the card waits for "next" after a mistake. */
  protected verdict = signal<ReviewCheck | null>(null);
  /** The option the learner picked (choice / listen) or the word typed. */
  protected given = signal('');
  private typeInput = viewChild<ElementRef<HTMLInputElement>>('typeInput');
  private nextButton = viewChild<ElementRef<HTMLButtonElement>>('nextButton');
  private advanceTimer: ReturnType<typeof setTimeout> | undefined;
  /** The learner's try at saying the word on screen. */
  protected said = signal<{ text: string; ok: boolean } | null>(null);
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
  protected quiz = computed(() => {
    const item = this.current();
    return item?.mode === 'review' ? (item.word.quiz ?? { mode: 'choice' as const }) : null;
  });

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.advanceTimer));
    // A new review card: listening plays the word, typing puts the cursor in the field.
    effect(() => {
      const quiz = this.quiz();
      const item = this.current();
      if (!quiz || !item || this.verdict()) return;
      if (quiz.mode === 'listen') setTimeout(() => this.speech.speak(item.word.word, 0.85), 250);
      // After rendering: the new card is in view and, for typing, the cursor is in the field.
      setTimeout(() => {
        document.querySelector('.word-card')?.scrollIntoView({ block: 'nearest' });
        if (quiz.mode === 'type') this.typeInput()?.nativeElement.focus({ preventScroll: true });
      });
    });
  }

  async ngOnInit() {
    await this.load();
  }

  protected async load() {
    this.loading.set(true);
    this.loadFailed.set(false);
    this.error.set('');
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
      this.verdict.set(null);
    } catch {
      this.loadFailed.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  /** Pronunciation: the recogniser should hear the word itself (case and punctuation aside). */
  protected pronounced(word: string, text: string) {
    const clean = (s: string) => s.toLowerCase().replace(/[^a-z' ]/g, '').trim();
    const heard = clean(text);
    this.said.set({ text, ok: heard === clean(word) || heard.split(' ').includes(clean(word)) });
  }

  protected listen() {
    const item = this.current();
    if (item) this.speech.speak(item.word.word, 0.85);
  }

  /** Review card: the server checks the pick (or typed word); an empty answer is "I don't know". */
  protected async check(answer: string) {
    const item = this.current();
    const quiz = this.quiz();
    if (!item || !quiz || this.busy() || this.verdict()) return;
    this.busy.set(true);
    this.error.set('');
    this.given.set(answer);
    try {
      const res = await firstValueFrom(this.api.checkReview(item.word.id, quiz.mode, answer));
      this.verdict.set(res);
      this.store.refresh();
      if (res.correct) {
        this.speech.speak(item.word.word, 0.9);
        this.note.set(this.noteFor('remember', res.status, res.next_review_date));
        if (!res.almost) this.advanceTimer = setTimeout(() => this.next(), 1100);
      } else {
        this.note.set($localize`Сөз ${res.stage}:stage:-кезеңге оралды, соңында тағы көрсетеміз.`);
      }
      queueMicrotask(() => this.nextButton()?.nativeElement.focus());
    } catch (e) {
      this.error.set(apiErrors(e).general);
      this.given.set('');
    } finally {
      this.busy.set(false);
    }
  }

  /** After the verdict: a right word leaves the queue, a forgotten one comes back at the end of the session. */
  protected next() {
    clearTimeout(this.advanceTimer);
    const item = this.current();
    const res = this.verdict();
    if (!item || !res) return;
    const rest = this.queue().slice(1);
    if (res.correct) {
      this.queue.set(rest);
      this.done.update((d) => d + 1);
    } else {
      this.queue.set([...rest, { word: { ...item.word, stage: res.stage }, mode: 'review' }]);
    }
    this.verdict.set(null);
    this.given.set('');
    this.said.set(null);
    if (!res.correct) this.note.set(''); // the "comes back later" hint belonged to the previous card
  }

  protected submitTyped(event: Event) {
    event.preventDefault();
    if (this.verdict()) {
      this.next();
      return;
    }
    const value = this.typeInput()?.nativeElement.value.trim() ?? '';
    if (value) this.check(value);
  }

  protected async answer(answer: 'start' | 'known') {
    const item = this.current();
    if (!item || this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.api.answer(item.word.id, answer));
      this.queue.set(this.queue().slice(1));
      this.done.update((d) => d + 1);
      this.said.set(null);
      this.note.set(this.noteFor(answer, res.status, res.next_review_date));
      if (answer === 'start') this.newLeft.update((n) => Math.max(0, n - 1));
      this.store.refresh();
    } catch (e) {
      this.error.set(apiErrors(e).general);
      if (e instanceof HttpErrorResponse && e.error?.code === 'limit') {
        // Limit reached: drop the remaining new words from today's queue. Other errors keep the card for a retry.
        this.queue.update((q) => q.filter((i) => i.mode !== 'new'));
        this.newLeft.set(0);
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
