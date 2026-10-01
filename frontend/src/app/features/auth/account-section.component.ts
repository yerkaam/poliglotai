import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ConfirmService } from '../../core/confirm.service';
import { ToastService } from '../../core/toast.service';
import { IconComponent } from '../../shared/icon.component';
import { apiErrors } from './errors';
import { PasswordInputComponent } from './password-input.component';

type Panel = 'password' | 'delete' | null;

/** Settings → account: change the password, download one's data, delete the account. */
@Component({
  selector: 'app-account-section',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, PasswordInputComponent, IconComponent],
  template: `
    <fieldset>
      <legend i18n>Аккаунт</legend>
      <p class="muted email">{{ auth.user()?.email }}</p>

      <div class="actions">
        <button type="button" class="btn btn-outline" [attr.aria-expanded]="panel() === 'password'"
                aria-controls="passwordPanel" (click)="toggle('password')" i18n>Құпиясөзді өзгерту</button>
        <button type="button" class="btn btn-outline" [disabled]="exporting()" (click)="download()" i18n>
          Деректерімді жүктеу</button>
      </div>

      @if (panel() === 'password') {
        <form id="passwordPanel" class="form panel" [formGroup]="pw" (ngSubmit)="changePassword()" novalidate>
          @if (pwError()) { <div class="alert" role="alert"><app-icon name="alert" /><span>{{ pwError() }}</span></div> }
          <div class="field">
            <label for="oldPassword" i18n>Ағымдағы құпиясөз</label>
            <app-password-input inputId="oldPassword" formControlName="old" autocomplete="current-password"
                                [invalid]="!!pwFields()['old_password']" describedBy="oldPasswordError" />
            @if (pwFields()['old_password']; as e) { <span class="field-error" id="oldPasswordError">{{ e }}</span> }
          </div>
          <div class="field">
            <label for="changePassword" i18n>Жаңа құпиясөз</label>
            <app-password-input inputId="changePassword" formControlName="password" autocomplete="new-password"
                                [invalid]="!!pwFields()['password']" describedBy="changeRules" />
            <div class="rules" id="changeRules" aria-live="polite">
              <span [class.ok]="longEnough()"><app-icon [name]="longEnough() ? 'check' : 'close'" [size]="14" [stroke]="3" />
                <ng-container i18n>Кемінде 8 таңба</ng-container></span>
              <span [class.ok]="hasDigit()"><app-icon [name]="hasDigit() ? 'check' : 'close'" [size]="14" [stroke]="3" />
                <ng-container i18n>Кемінде 1 сан</ng-container></span>
            </div>
            @if (pwFields()['password']; as e) { <span class="field-error">{{ e }}</span> }
          </div>
          <div class="field">
            <label for="changePassword2" i18n>Жаңа құпиясөзді қайталаңыз</label>
            <app-password-input inputId="changePassword2" formControlName="password2" autocomplete="new-password"
                                [invalid]="mismatch()" />
            @if (mismatch()) { <span class="field-error" i18n>Құпиясөздер сәйкес емес.</span> }
          </div>
          <small class="muted" i18n>Басқа құрылғылардан шығып кетесіз, осы құрылғыда кіру сақталады.</small>
          <button type="submit" class="btn btn-primary" [disabled]="busy() || !canChange()" i18n>Құпиясөзді сақтау</button>
        </form>
      }

      <div class="danger">
        @if (panel() !== 'delete') {
          <button type="button" class="btn btn-ghost delete-link" aria-controls="deletePanel" aria-expanded="false"
                  (click)="toggle('delete')" i18n>Аккаунтты жою</button>
        } @else {
          <form id="deletePanel" class="form panel" (submit)="deleteAccount($event)" novalidate>
            <h3 class="danger-title" i18n>Аккаунтты жою</h3>
            <p class="muted" i18n>
              Сөздер, курс нәтижелері, чат тарихы және бүкіл прогресс біржола өшеді, оны қалпына келтіру мүмкін емес.
              Алдымен «Деректерімді жүктеу» арқылы көшірмесін сақтап алуға болады.
            </p>
            @if (auth.user()?.is_teacher) {
              <p class="muted" i18n>Сіз құрған топтар да жойылады, оқушылар олардан шығып қалады.</p>
            }
            @if (delError()) { <div class="alert" role="alert"><app-icon name="alert" /><span>{{ delError() }}</span></div> }
            <div class="field">
              <label for="deletePassword" i18n>Растау үшін құпиясөз</label>
              <app-password-input inputId="deletePassword" [formControl]="deletePassword" autocomplete="current-password" />
            </div>
            <div class="row">
              <button type="submit" class="btn btn-primary" [disabled]="busy() || !deletePassword.value" i18n>
                Біржола жою</button>
              <button type="button" class="btn btn-ghost" (click)="toggle(null)" i18n>Бас тарту</button>
            </div>
          </form>
        }
      </div>
    </fieldset>
  `,
  styleUrl: './auth.scss',
  styles: `
    .email { margin: 0; overflow-wrap: anywhere; }
    .actions { display: grid; gap: 8px; }
    .panel { padding: 14px; border: 1px solid var(--line); border-radius: var(--r-md); }
    .danger { border-top: 1px solid var(--line); padding-top: 8px; }
    .delete-link { color: var(--red-strong); background: none; border-color: transparent; }
    .delete-link:hover { background: color-mix(in srgb, var(--red) 8%, transparent); }
    .danger-title { margin: 0; font-size: 17px; color: var(--red-strong); }
    .row { display: flex; flex-wrap: wrap; gap: 8px; }
    .row .btn { flex: 1 1 auto; white-space: nowrap; }
  `,
})
export class AccountSectionComponent {
  protected auth = inject(AuthService);
  private api = inject(ApiService);
  private toasts = inject(ToastService);
  private confirm = inject(ConfirmService);
  private fb = inject(FormBuilder);

  protected panel = signal<Panel>(null);
  protected busy = signal(false);
  protected exporting = signal(false);
  protected pwError = signal('');
  protected pwFields = signal<Record<string, string>>({});
  protected delError = signal('');

  protected pw = this.fb.nonNullable.group({
    old: ['', Validators.required],
    password: ['', Validators.required],
    password2: ['', Validators.required],
  });
  protected deletePassword = this.fb.nonNullable.control('');
  private value = toSignal(this.pw.valueChanges, { initialValue: this.pw.getRawValue() });
  protected longEnough = computed(() => (this.value().password ?? '').length >= 8);
  protected hasDigit = computed(() => /\d/.test(this.value().password ?? ''));
  protected mismatch = computed(() => !!this.value().password2 && this.value().password !== this.value().password2);
  protected canChange = computed(
    () => !!this.value().old && this.longEnough() && this.hasDigit() && this.value().password === this.value().password2,
  );

  protected toggle(panel: Panel) {
    this.panel.set(this.panel() === panel ? null : panel);
    this.pw.reset();
    this.deletePassword.reset();
    this.pwError.set('');
    this.pwFields.set({});
    this.delError.set('');
  }

  protected async changePassword() {
    if (!this.canChange() || this.busy()) return;
    this.busy.set(true);
    this.pwError.set('');
    this.pwFields.set({});
    const { old, password, password2 } = this.pw.getRawValue();
    try {
      const res = await firstValueFrom(this.api.changePassword(old, password, password2));
      this.toasts.success(res.detail);
      this.toggle(null);
    } catch (e) {
      const errors = apiErrors(e);
      this.pwFields.set(errors.fields);
      // a wrong current password is shown at its field; the general line would only repeat it
      if (!errors.fields['old_password']) this.pwError.set(errors.general);
    } finally {
      this.busy.set(false);
    }
  }

  protected async download() {
    this.exporting.set(true);
    try {
      const blob = await firstValueFrom(this.api.exportData());
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `poliglotai-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      this.toasts.success($localize`Деректер файлы жүктелді.`);
    } catch (e) {
      const message = apiErrors(e).general;
      if (message) this.toasts.error(message);
    } finally {
      this.exporting.set(false);
    }
  }

  protected async deleteAccount(event: Event) {
    event.preventDefault();
    if (!this.deletePassword.value || this.busy()) return;
    const ok = await this.confirm.ask({
      title: $localize`Аккаунтты біржола жою керек пе?`,
      message: $localize`Барлық сөздер, прогресс пен чат тарихы өшеді. Бұл әрекетті болдырмау мүмкін емес.`,
      confirmText: $localize`Иә, жою`,
      cancelText: $localize`Бас тарту`,
    });
    if (!ok) return;
    this.busy.set(true);
    this.delError.set('');
    try {
      await firstValueFrom(this.api.deleteAccount(this.deletePassword.value));
      this.toasts.success($localize`Аккаунт жойылды. Сау болыңыз!`);
      await this.auth.clear('/register');
    } catch (e) {
      const errors = apiErrors(e);
      this.delError.set(errors.fields['password'] || errors.general);
    } finally {
      this.busy.set(false);
    }
  }
}
