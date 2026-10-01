import { HttpErrorResponse } from '@angular/common/http';
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

/**
 * One course step as a guided path: short lessons one at a time (a rule, examples, practice with the reason
 * shown at once), then the final check. Passing the check opens the next step.
 */
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

  /** Which stage is on screen: 0…lessons-1 are the lessons, `lessons` is the final check. */
  protected current = signal(0);
  /** The furthest stage the learner has reached (stages up to it can be revisited). */
  protected reached = signal(0);
  /** Practice answers of the lesson on screen: question index → chosen option. */
  protected picked = signal<Record<number, string>>({});

  protected answers = signal<string[]>([]);
  protected result = signal<StepCheckResult | null>(null);
  protected checking = signal(false);
  protected error = signal('');

  protected lessonCount = computed(() => this.step()?.lesson.length ?? 0);
  protected onCheck = computed(() => this.current() >= this.lessonCount());
  protected lesson = computed(() => this.step()?.lesson[this.current()] ?? null);
  protected stages = computed(() => Array.from({ length: this.lessonCount() + 1 }, (_, i) => i));
  protected practiceDone = computed(() => {
    const practice = this.lesson()?.practice ?? [];
    const picked = this.picked();
    return practice.every((_, i) => picked[i] !== undefined);
  });
  protected answeredCount = computed(() => this.answers().filter((a) => a.trim()).length);
  protected allAnswered = computed(() => {
    const s = this.step();
    return !!s && this.answeredCount() === s.exercises.length;
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
    return $localize`Тесттен шығасыз ба?`;
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
      // Resume where the learner stopped; a finished step opens on its first lesson for review.
      const resume = step.status === 'done' ? 0 : Math.min(step.lessons_done, step.lesson.length);
      this.reached.set(step.status === 'done' ? step.lesson.length : resume);
      this.show(resume);
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

  /** Opens a stage the learner has already reached. */
  protected show(stage: number) {
    if (stage > this.reached()) return;
    this.current.set(stage);
    this.picked.set({});
    queueMicrotask(() => document.getElementById('stage')?.scrollIntoView({ block: 'start', behavior: 'smooth' }));
  }

  protected pick(question: number, option: string) {
    if (this.picked()[question] !== undefined) return;
    this.picked.update((p) => ({ ...p, [question]: option }));
  }

  protected tryAgain(question: number) {
    this.picked.update((p) => {
      const next = { ...p };
      delete next[question];
      return next;
    });
  }

  /** Lesson finished: remember it on the server (to resume later) and go on. */
  protected next() {
    const step = this.step();
    if (!step || !this.practiceDone()) return;
    const stage = this.current() + 1;
    if (stage > this.reached()) {
      this.reached.set(stage);
      this.api.saveLessons(step.number, stage).subscribe({ error: () => undefined });
    }
    this.show(stage);
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
      if (result.opened_step) this.toasts.success($localize`${result.opened_step}:step:-қадам ашылды!`);
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
    queueMicrotask(() => document.getElementById('stage')?.scrollIntoView({ block: 'start' }));
  }

  protected goTo(n: number) {
    this.router.navigate(['/course', n]);
  }
}
