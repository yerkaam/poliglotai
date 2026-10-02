import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { catchError, filter, of, switchMap } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { apiResource } from '../../core/api-resource';
import { AuthService } from '../../core/auth.service';
import { INTERVAL_LABELS, PRONOUNS, capitalize } from '../../core/labels';
import { CourseStep, GoalTask, Pronoun, VerbForms, Word } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { IconComponent } from '../../shared/icon.component';
import { LoadErrorComponent } from '../../shared/load-error.component';
import { VerbGridComponent } from '../../shared/verb-grid.component';

const TASK_ROUTE: Record<GoalTask['key'], string> = {
  reviews: '/words',
  new: '/words',
  trainer: '/trainer',
  chat: '/chat',
};

const SCENARIO_KK: Record<string, string> = {
  cafe: $localize`Кафеде`,
  meet: $localize`Танысу`,
  airport: $localize`Әуежайда`,
  shop: $localize`Дүкенде`,
  interview: $localize`Сұхбат`,
};

@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, RouterLink, VerbGridComponent, DatePipe, LoadErrorComponent],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  private api = inject(ApiService);
  private router = inject(Router);
  protected auth = inject(AuthService);
  protected store = inject(ProgressStore);

  protected today = new Date();
  protected pronouns = PRONOUNS;
  protected intervals = INTERVAL_LABELS;
  protected capitalize = capitalize;
  protected pronoun = signal<Pronoun>('she');

  protected verbs = apiResource(() => this.api.verbs(), [] as Word[]);
  protected course = apiResource(() => this.api.course(), [] as CourseStep[]);
  /** Three steps around the learner's current one: the last done, the open one, the next locked. */
  protected nearSteps = computed(() => {
    const steps = this.course.value();
    const current = steps.findIndex((s) => s.status === 'open');
    const start = Math.max(0, Math.min((current < 0 ? 0 : current) - 1, steps.length - 3));
    return steps.slice(start, start + 3);
  });

  /** Verb of the day: rotates daily through the verbs being learned (or the course verbs). */
  protected verbOfDay = computed<Word | null>(() => {
    const all = this.verbs.value().filter((v) => v.is_verb && v.course_step !== null);
    if (!all.length) return null;
    const learning = all.filter((v) => v.status === 'learning');
    const pool = learning.length ? learning : all;
    const day = Math.floor(Date.now() / 86400000);
    return pool[day % pool.length];
  });

  private request = computed(() => {
    const v = this.verbOfDay();
    return v ? { id: v.id, pronoun: this.pronoun() } : null;
  });

  protected forms = toSignal(
    toObservable(this.request).pipe(
      filter((r) => r !== null),
      switchMap((r) => this.api.forms(r.id, r.pronoun).pipe(catchError(() => of(null)))),
    ),
    { initialValue: null as VerbForms | null },
  );

  protected goal = computed(() => this.store.progress()?.goal ?? null);
  protected minutes = computed(() => this.auth.user()?.profile.daily_minutes ?? 15);
  protected goalPercent = computed(() => {
    const g = this.goal();
    return g && g.total ? Math.round((100 * g.done) / g.total) : 0;
  });
  protected stageMax = computed(() => Math.max(1, ...(this.store.progress()?.stages.map((s) => s.count) ?? [1])));

  protected taskLabel(task: GoalTask): string {
    switch (task.key) {
      case 'reviews':
        return $localize`${task.target}:count: сөзді қайталау`;
      case 'new':
        return $localize`${task.target}:count: жаңа сөз`;
      case 'trainer':
        return $localize`Жаттықтырғыш: ${task.target}:count: сөйлем`;
      case 'chat':
        return $localize`AI-чат: «${SCENARIO_KK[task.scenario ?? 'cafe']}:scenario:» диалогы`;
    }
  }

  protected taskRoute(task: GoalTask) {
    return TASK_ROUTE[task.key];
  }

  /** "Continue" opens the first unfinished task of the day. */
  protected continueDay() {
    const next = this.goal()?.tasks.find((t) => !t.complete);
    this.router.navigateByUrl(next ? TASK_ROUTE[next.key] : '/trainer');
  }
}
