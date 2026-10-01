import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { PwaService } from '../../core/pwa.service';
import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { firstValueFrom } from 'rxjs';
import { MyGroup } from '../../core/models';
import { Level } from '../../core/models';
import { AccountSectionComponent } from './account-section.component';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';

type Limit = 5 | 10 | 15 | 20;
const MINUTES: Record<Limit, number> = { 5: 10, 10: 15, 15: 20, 20: 25 };

/** AUTH-04: after registration the learner picks a level and a daily goal; later the same screen is the settings. */
@Component({
  selector: 'app-onboarding',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayoutComponent, AccountSectionComponent, RouterLink],
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

      @if (editing) {
        <fieldset>
          <legend i18n>Мұғалім тобы</legend>
          @if (auth.user()?.is_teacher) {
            <a class="btn btn-outline" routerLink="/teacher" i18n>Мұғалім кабинетін ашу</a>
          }
          @for (g of myGroups(); track g.id) {
            <div class="group-row">
              <span><b>{{ g.name }}</b> <small class="muted">· {{ g.teacher }}</small></span>
              <button type="button" class="btn btn-ghost" (click)="leave(g)" i18n>Шығу</button>
            </div>
          }
          <form class="join" (submit)="join($event)">
            <label for="groupCode" class="visually-hidden" i18n>Мұғалім берген код</label>
            <input id="groupCode" class="input mono" maxlength="8" autocapitalize="characters" autocomplete="off"
                   i18n-placeholder placeholder="Мұғалім берген код"
                   [value]="code()" (input)="code.set($any($event.target).value)" />
            <button type="submit" class="btn btn-outline" [disabled]="code().trim().length < 6 || joining()" i18n>Қосылу</button>
          </form>
          @if (joinError()) {
            <div class="alert" role="alert">{{ joinError() }}</div>
          }
          <small class="muted" i18n>
            Мұғалім сіздің прогресіңізді көреді: соңғы сабақ, сөздер саны, курс қадамы, жаттықтырғыштағы дәлдік және
            жиі кездесетін қателер. AI-чаттағы хабарламаларыңызды көрмейді. Топтан кез келген уақытта шыға аласыз.
          </small>
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
        <app-account-section />
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
    .group-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 6px 0;
      border-bottom: 1px solid var(--line); }
    .join { display: flex; gap: 8px; }
    .join .input { flex: 1; min-width: 0; text-transform: uppercase; letter-spacing: 0.1em; }
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
  private api = inject(ApiService);
  private toasts = inject(ToastService);
  protected myGroups = signal<MyGroup[]>([]);
  protected code = signal('');
  protected joining = signal(false);
  protected joinError = signal('');
  protected editing = !!this.auth.user()?.profile.onboarded;
  protected hours = [8, 12, 18, 19, 20, 21];
  protected reminders = signal(this.auth.user()?.profile.reminder_enabled ?? true);
  protected hour = signal(this.auth.user()?.profile.reminder_hour ?? 19);

  constructor() {
    if (this.editing) this.api.myGroups().subscribe({ next: (g) => this.myGroups.set(g), error: () => undefined });
  }

  protected async join(event: Event) {
    event.preventDefault();
    this.joining.set(true);
    this.joinError.set('');
    try {
      const group = await firstValueFrom(this.api.joinGroup(this.code()));
      this.myGroups.update((list) => (list.some((g) => g.id === group.id) ? list : [...list, group]));
      this.code.set('');
      this.toasts.success($localize`«${group.name}:name:» тобына қосылдыңыз.`);
    } catch (e) {
      const errors = apiErrors(e);
      this.joinError.set(errors.fields['code'] || errors.general);
    } finally {
      this.joining.set(false);
    }
  }

  protected async leave(group: MyGroup) {
    await firstValueFrom(this.api.leaveGroup(group.id));
    this.myGroups.update((list) => list.filter((g) => g.id !== group.id));
    this.toasts.success($localize`«${group.name}:name:» тобынан шықтыңыз.`);
  }

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
