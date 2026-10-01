import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { PwaService } from '../../core/pwa.service';
import { Level } from '../../core/models';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';

type Limit = 5 | 10 | 15 | 20;
const MINUTES: Record<Limit, number> = { 5: 10, 10: 15, 15: 20, 20: 25 };

/** AUTH-04: after registration the learner picks a level and a daily goal; later the same screen is the settings. */
@Component({
  selector: 'app-onboarding',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayoutComponent, RouterLink],
  template: `
    <app-auth-layout>
      <div class="intro">
        @if (editing) {
          <h2 class="page-title" i18n>Баптаулар</h2>
          <p class="muted" i18n>Деңгей мен күнделікті жаңа сөздер санын кез келген уақытта өзгертуге болады.</p>
        } @else {
          <h2 class="page-title" i18n>Сәлем, {{ auth.user()?.name }}!</h2>
          <p class="muted" i18n>Екі сұрақ — және бастаймыз.</p>
        }
      </div>

      <fieldset>
        <legend i18n>Ағылшын тілін қаншалықты білесіз?</legend>
        <div class="options">
          <button type="button" [attr.aria-pressed]="level() === 'A0'" (click)="level.set('A0')">
            <b>A0</b><small i18n>Нөлден бастаймын</small>
          </button>
          <button type="button" [attr.aria-pressed]="level() === 'A1'" (click)="level.set('A1')">
            <b>A1</b><small i18n>Мектепте оқығанмын</small>
          </button>
        </div>
        <a class="placement-link" routerLink="/placement">
          <b i18n>Сенімді емеспін — тестпен анықтайық</b>
          <small i18n>3–4 минут. Білетін қадамдарыңыз есептеледі.</small>
        </a>
      </fieldset>

      <fieldset>
        <legend i18n>Күніне қанша жаңа сөз?</legend>
        <div class="options four">
          @for (n of limits; track n) {
            <button type="button" [attr.aria-pressed]="limit() === n" (click)="limit.set(n)">
              <b>{{ n }}</b><small>{{ minutes(n) }}</small>
            </button>
          }
        </div>
      </fieldset>

      @if (editing) {
        <fieldset>
          <legend i18n>Еске салғыш хат</legend>
          <label class="check">
            <input type="checkbox" [checked]="reminders()" (change)="reminders.set($any($event.target).checked)" />
            <span i18n>Сабақ болмаған күні поштаға еске салу</span>
          </label>
          @if (reminders()) {
            <div class="options six" role="group" i18n-aria-label aria-label="Хат уақыты">
              @for (h of hours; track h) {
                <button type="button" [attr.aria-pressed]="hour() === h" (click)="hour.set(h)">
                  <b>{{ h }}:00</b>
                </button>
              }
            </div>
            <small class="muted" i18n>Алматы уақыты бойынша. Сол күні сабақ болса, хат келмейді.</small>
          }
        </fieldset>
      }

      @if (editing && (pwa.canInstall() || pwa.iosHint() || pwa.installed())) {
        <fieldset>
          <legend i18n>Телефондағы қосымша</legend>
          @if (pwa.installed()) {
            <p class="muted" i18n>PoliglotAi осы құрылғыда қосымша ретінде орнатылған.</p>
          } @else if (pwa.canInstall()) {
            <p class="muted" i18n>Басты экраннан бір басумен ашылады, интернетсіз де карточкаларды қайталауға болады.</p>
            <button type="button" class="btn btn-outline" (click)="pwa.install()" i18n>Телефонға орнату</button>
          } @else {
            <p class="muted" i18n>iPhone-да: Safari-де «Бөлісу» батырмасын басып, «Басты экранға қосу» таңдаңыз.</p>
          }
        </fieldset>
      }

      @if (error()) { <div class="alert" role="alert">{{ error() }}</div> }
      @if (editing) {
        <button type="button" class="btn btn-primary btn-lg" [disabled]="busy()" (click)="save()" i18n>Сақтау</button>
        <a class="btn btn-ghost btn-lg" routerLink="/" i18n>Артқа</a>
      } @else {
        <button type="button" class="btn btn-primary btn-lg" [disabled]="busy()" (click)="save()" i18n>Бастау</button>
      }
    </app-auth-layout>
  `,
  styleUrl: './auth.scss',
  styles: `
    .placement-link { display: flex; flex-direction: column; gap: 2px; padding: 12px; border-radius: var(--r-md);
      border: 1.5px dashed var(--line); color: var(--ink); text-decoration: none; }
    .placement-link:hover { border-color: var(--ink); }
    .placement-link small { color: var(--muted); font-size: 13px; }
  `,
})
export class OnboardingComponent {
  protected auth = inject(AuthService);
  private router = inject(Router);

  protected limits: Limit[] = [5, 10, 15, 20];
  protected level = signal<Level>(this.auth.user()?.profile.level ?? 'A0');
  protected limit = signal<Limit>(this.auth.user()?.profile.daily_new_limit ?? 10);
  protected busy = signal(false);
  protected error = signal('');
  /** Opened from the menu after onboarding: the same choices, as settings. */
  protected pwa = inject(PwaService);
  protected editing = !!this.auth.user()?.profile.onboarded;
  protected hours = [8, 12, 18, 19, 20, 21];
  protected reminders = signal(this.auth.user()?.profile.reminder_enabled ?? true);
  protected hour = signal(this.auth.user()?.profile.reminder_hour ?? 19);

  protected minutes(n: Limit) {
    return $localize`~${MINUTES[n]}:minutes: мин`;
  }

  async save() {
    this.busy.set(true);
    this.error.set('');
    try {
      const n = this.limit();
      await this.auth.updateProfile({
        level: this.level(),
        daily_new_limit: n,
        daily_minutes: MINUTES[n],
        onboarded: true,
        ...(this.editing ? { reminder_enabled: this.reminders(), reminder_hour: this.hour() } : {}),
      });
      await this.router.navigate(['/']);
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.busy.set(false);
    }
  }
}
