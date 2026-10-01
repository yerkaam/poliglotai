import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { GuardedPage } from '../../core/leave.guard';
import { PlacementQuestion, PlacementResult } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { AuthLayoutComponent } from '../auth/auth-layout.component';
import { apiErrors } from '../auth/errors';

/** "I don't know" this many times in a row ends the test: the rest would be harder still. */
const GIVE_UP_AFTER = 3;

/** The placement test: one question at a time, then the level and the course steps it credits. */
@Component({
  selector: 'app-placement',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayoutComponent, RouterLink],
  template: `
    <app-auth-layout>
      @if (result(); as r) {
        <div class="intro">
          <span class="eyebrow" i18n>Нәтиже</span>
          <h2 class="page-title" i18n>Сіздің деңгейіңіз: {{ r.level }}</h2>
          <p class="muted" i18n>{{ r.score }} / {{ r.total }} дұрыс жауап.</p>
        </div>
        @if (r.steps_credited.length) {
          <div class="alert alert-ok" role="status">
            <span i18n>Курстың {{ stepsText(r.steps_credited) }} есептелді — оларды қайта өтудің қажеті жоқ. {{ next(r) }}-қадамнан бастаймыз.</span>
          </div>
        } @else {
          <p i18n>Курсты басынан — негізгі кестеден бастаймыз. Бұл дұрыс таңдау: әр қадам қысқа, түсінікті.</p>
        }
        <button type="button" class="btn btn-primary btn-lg" (click)="continue()" i18n>Жалғастыру</button>
      } @else if (started() && current(); as q) {
        <div class="progress-track" role="progressbar" [attr.aria-valuenow]="index() + 1" aria-valuemin="1"
             [attr.aria-valuemax]="questions().length">
          <span [style.width.%]="(100 * index()) / questions().length"></span>
        </div>
        <span class="eyebrow" i18n>Сұрақ {{ index() + 1 }} / {{ questions().length }}</span>
        <p class="prompt"><b>{{ q.prompt }}</b><br /><span class="muted">{{ q.prompt_kk }}</span></p>
        <div class="choices" role="group" [attr.aria-label]="q.prompt">
          @for (o of q.options; track o) {
            <button type="button" class="choice" [disabled]="busy()" (click)="answer(o)">{{ o }}</button>
          }
        </div>
        <button type="button" class="btn btn-ghost" [disabled]="busy()" (click)="answer('')" i18n>Білмеймін</button>
        @if (error()) {
          <div class="alert" role="alert">{{ error() }}</div>
        }
        <button type="button" class="link" [disabled]="busy()" (click)="finish()" i18n>Тестті осы жерде аяқтау</button>
      } @else {
        <div class="intro">
          <span class="eyebrow" i18n>3–4 минут</span>
          <h2 class="page-title" i18n>Деңгейді анықтайық</h2>
          <p class="muted" i18n>
            {{ questions().length || 22 }} қысқа сұрақ — оңайдан қиынға. Жауабын білмесеңіз, «Білмеймін» басыңыз: бұл
            емтихан емес. Білетін қадамдарыңыз есептеледі, курсты соларсыз жалғастырасыз.
          </p>
        </div>
        @if (error()) {
          <div class="alert" role="alert">{{ error() }}</div>
        }
        <button type="button" class="btn btn-primary btn-lg" [disabled]="!questions().length" (click)="started.set(true)" i18n>
          Бастау
        </button>
        <a class="btn btn-ghost" [routerLink]="back()" i18n>Артқа</a>
      }
    </app-auth-layout>
  `,
  styleUrl: '../auth/auth.scss',
  styles: `
    .prompt { margin: 4px 0 0; font-size: 18px; line-height: 1.4; }
    .choices { display: grid; gap: 10px; }
    .choice { min-height: 52px; border-radius: var(--r-md); border: 1.5px solid var(--line); background: var(--surface);
      font-size: 17px; font-weight: 600; color: var(--ink); }
    .choice:hover:not(:disabled) { border-color: var(--ink); }
    .link { border: 0; background: none; color: var(--muted); font-size: 14px; min-height: 44px; text-decoration: underline; }
  `,
})
export class PlacementComponent extends GuardedPage {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private store = inject(ProgressStore);

  protected questions = signal<PlacementQuestion[]>([]);
  protected started = signal(false);
  protected answers = signal<string[]>([]);
  protected result = signal<PlacementResult | null>(null);
  protected busy = signal(false);
  protected error = signal('');
  private dontKnowRun = 0;

  protected index = computed(() => this.answers().length);
  protected current = computed(() => this.questions()[this.index()] ?? null);
  protected onboarded = computed(() => !!this.auth.user()?.profile.onboarded);
  protected back = computed(() => (this.onboarded() ? '/settings' : '/onboarding'));

  constructor() {
    super();
    this.load();
  }

  hasUnsavedWork() {
    return this.started() && !this.result() && this.answers().length > 0;
  }

  override leaveMessage() {
    return $localize`Тест аяқталмады, нәтиже сақталмайды.`;
  }

  private async load() {
    try {
      this.questions.set((await firstValueFrom(this.api.placement())).questions);
    } catch (e) {
      this.error.set(apiErrors(e).general);
    }
  }

  protected answer(option: string) {
    this.answers.update((a) => [...a, option]);
    this.dontKnowRun = option ? 0 : this.dontKnowRun + 1;
    if (this.dontKnowRun >= GIVE_UP_AFTER || this.index() >= this.questions().length) this.finish();
  }

  /** Sends what was answered; the rest counts as not known. */
  protected async finish() {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    try {
      const result = await firstValueFrom(this.api.submitPlacement(this.answers()));
      // The profile first: "continue" must already see the new level.
      await this.auth.reload();
      this.result.set(result);
      this.store.refresh();
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.busy.set(false);
    }
  }

  protected stepsText(steps: number[]) {
    return steps.length === 1 ? $localize`1-қадамы` : $localize`1–${steps[steps.length - 1]}:last:-қадамдары`;
  }

  protected next(r: PlacementResult) {
    return Math.min(16, r.steps_credited.length + 1);
  }

  protected continue() {
    this.router.navigateByUrl(this.onboarded() ? '/course' : '/onboarding');
  }
}
