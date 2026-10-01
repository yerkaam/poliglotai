import { ChangeDetectionStrategy, Component, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { GuardedPage } from '../../core/leave.guard';
import { StepCheckResult, StepDetail } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { SpeechService } from '../../core/speech.service';
import { ToastService } from '../../core/toast.service';
import { IconComponent } from '../../shared/icon.component';
import { LoadErrorComponent } from '../../shared/load-error.component';
import { apiErrors } from '../auth/errors';
import { HttpErrorResponse } from '@angular/common/http';

/** One course step: the lesson, its words, and the check that (with the words started) opens the next step. */
@Component({
  selector: 'app-step',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, RouterLink, LoadErrorComponent],
  templateUrl: './step.component.html',
  styleUrl: './step.component.scss',
})
export class StepComponent extends GuardedPage {
  private api = inject(ApiService);
  private router = inject(Router);
  private toasts = inject(ToastService);
  private store = inject(ProgressStore);
  protected speech = inject(SpeechService);

  /** Route parameter (/course/:number). */
  readonly number = input.required<string>();

  protected step = signal<StepDetail | null>(null);
  protected loading = signal(true);
  protected failed = signal(false);
  protected locked = signal(false);
  protected answers = signal<string[]>([]);
  protected result = signal<StepCheckResult | null>(null);
  protected checking = signal(false);
  protected error = signal('');

  protected answeredCount = computed(() => this.answers().filter((a) => a.trim()).length);
  protected allAnswered = computed(() => {
    const s = this.step();
    return !!s && this.answeredCount() === s.exercises.length;
  });
  /** The words part of "done": enough of the step's words started in the cards. */
  protected wordsOk = computed(() => {
    const s = this.result()?.step ?? this.step();
    return !!s && s.words_started >= s.words_needed;
  });
  protected quizOk = computed(() => {
    const s = this.result()?.step ?? this.step();
    return !!s && (s.quiz_passed || s.quiz_total === 0);
  });
  protected status = computed(() => this.result()?.step.status ?? this.step()?.status ?? 'open');

  constructor() {
    super();
    // A new step number (e.g. "go to step 3" after a pass) loads that step on the same screen.
    effect(() => {
      const n = Number(this.number());
      untracked(() => this.load(n));
    });
  }

  hasUnsavedWork() {
    return this.answeredCount() > 0 && !this.result();
  }

  override leaveTitle() {
    return $localize`Тексеруден шығасыз ба?`;
  }

  override leaveMessage() {
    return $localize`Берілген жауаптар тексерілмей қалады.`;
  }

  protected async load(n: number) {
    this.loading.set(true);
    this.failed.set(false);
    this.locked.set(false);
    this.result.set(null);
    this.error.set('');
    try {
      const step = await firstValueFrom(this.api.step(n));
      this.step.set(step);
      this.answers.set(step.exercises.map(() => ''));
    } catch (e) {
      this.step.set(null);
      if (e instanceof HttpErrorResponse && e.status === 403) this.locked.set(true);
      else this.failed.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected reload() {
    this.load(Number(this.number()));
  }

  protected setAnswer(index: number, value: string) {
    if (this.result()) return;
    this.answers.update((list) => list.map((a, i) => (i === index ? value : a)));
  }

  protected async check(event?: Event) {
    event?.preventDefault();
    const step = this.step();
    if (!step || !this.allAnswered() || this.checking()) return;
    this.checking.set(true);
    this.error.set('');
    try {
      const result = await firstValueFrom(this.api.checkStep(step.number, this.answers()));
      this.result.set(result);
      this.store.refresh();
      if (result.opened_step) {
        this.toasts.success($localize`${result.opened_step}:step:-қадам ашылды!`);
      }
      queueMicrotask(() => document.getElementById('checkResult')?.scrollIntoView({ block: 'center' }));
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.checking.set(false);
    }
  }

  protected retry() {
    const step = this.step();
    this.result.set(null);
    this.answers.set(step ? step.exercises.map(() => '') : []);
    queueMicrotask(() => document.getElementById('check')?.scrollIntoView({ block: 'start' }));
  }

  protected goTo(n: number) {
    this.router.navigate(['/course', n]);
  }
}
