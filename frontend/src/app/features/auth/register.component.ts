import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { IconComponent } from '../../shared/icon.component';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';
import { PasswordInputComponent } from './password-input.component';

@Component({
  selector: 'app-register',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, PasswordInputComponent, IconComponent],
  template: `
    <app-auth-layout>
      <div class="segmented" role="group" i18n-aria-label aria-label="Кіру немесе тіркелу">
        <button type="button" aria-pressed="false" routerLink="/login" i18n>Кіру</button>
        <button type="button" aria-pressed="true" i18n>Тіркелу</button>
      </div>
      <div class="intro">
        <h2 class="page-title" i18n>Тіркелу</h2>
        <p class="muted" i18n>Ағылшын тілін бүгіннен бастаңыз.</p>
      </div>

      @if (general()) {
        <div class="alert" role="alert"><app-icon name="alert" /><span>{{ general() }}</span></div>
      }

      <form [formGroup]="form" (ngSubmit)="submit()" class="form" novalidate>
        <div class="field">
          <label for="regName" i18n>Атыңыз</label>
          <input id="regName" class="input" name="name" formControlName="name" autocomplete="given-name"
                 [attr.aria-invalid]="!!fieldError('name') || null" aria-describedby="regNameErr" />
          @if (fieldError('name')) { <span id="regNameErr" class="field-error">{{ fieldError('name') }}</span> }
        </div>
        <div class="field">
          <label for="regEmail" i18n>Электрондық пошта</label>
          <input id="regEmail" class="input" type="email" name="email" formControlName="email" autocomplete="username"
                 placeholder="name@mail.kz" [attr.aria-invalid]="!!fieldError('email') || null" aria-describedby="regEmailErr" />
          @if (fieldError('email')) { <span id="regEmailErr" class="field-error" role="alert">{{ fieldError('email') }}</span> }
        </div>
        <div class="field">
          <label for="regPassword" i18n>Құпиясөз</label>
          <app-password-input inputId="regPassword" name="password" formControlName="password" autocomplete="new-password"
                              describedBy="regRules" [invalid]="!!fieldError('password')" />
          <!-- AUTH-02: rules are checked while typing -->
          <div class="rules" id="regRules" aria-live="polite">
            <span [class.ok]="longEnough()"><app-icon [name]="longEnough() ? 'check' : 'close'" [size]="14" [stroke]="3" />
              <ng-container i18n>Кемінде 8 таңба</ng-container></span>
            <span [class.ok]="hasDigit()"><app-icon [name]="hasDigit() ? 'check' : 'close'" [size]="14" [stroke]="3" />
              <ng-container i18n>Кемінде 1 сан</ng-container></span>
          </div>
          @if (fieldError('password')) { <span class="field-error">{{ fieldError('password') }}</span> }
        </div>
        <div class="field">
          <label for="regPassword2" i18n>Құпиясөзді қайталаңыз</label>
          <app-password-input inputId="regPassword2" name="password2" formControlName="password2" autocomplete="new-password"
                              [invalid]="mismatch() || !!fieldError('password2')" describedBy="regPassword2Err" />
          @if (mismatch() || fieldError('password2')) {
            <span id="regPassword2Err" class="field-error" i18n>Құпиясөздер сәйкес емес.</span>
          }
        </div>
        <label class="check">
          <input type="checkbox" formControlName="accept_terms" />
          <span i18n>Пайдалану шарттарымен және құпиялылық саясатымен келісемін</span>
        </label>
        @if (fieldError('accept_terms')) { <span class="field-error">{{ fieldError('accept_terms') }}</span> }
        <button type="submit" class="btn btn-primary btn-lg" [disabled]="busy()" i18n>Аккаунт ашу</button>
      </form>
      <p class="foot muted"><ng-container i18n>Аккаунтыңыз бар ма?</ng-container>&ngsp;<a routerLink="/login" i18n>Кіру</a></p>
    </app-auth-layout>
  `,
  styleUrl: './auth.scss',
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);

  protected busy = signal(false);
  protected general = signal('');
  protected serverErrors = signal<Record<string, string>>({});
  protected submitted = signal(false);

  protected form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
    password2: ['', Validators.required],
    accept_terms: [false, Validators.requiredTrue],
  });

  private value = toSignal(this.form.valueChanges, { initialValue: this.form.getRawValue() });
  protected longEnough = computed(() => (this.value().password ?? '').length >= 8);
  protected hasDigit = computed(() => /\d/.test(this.value().password ?? ''));
  protected mismatch = computed(() => {
    const v = this.value();
    return !!v.password2 && v.password !== v.password2;
  });

  protected fieldError(name: string): string {
    const server = this.serverErrors()[name];
    if (server) return server;
    if (!this.submitted()) return '';
    const control = this.form.get(name);
    if (!control?.invalid) return '';
    if (name === 'email') return $localize`Дұрыс пошта енгізіңіз.`;
    if (name === 'accept_terms') return $localize`Пайдалану шарттарымен келісу керек.`;
    return $localize`Толтырыңыз.`;
  }

  async submit() {
    this.submitted.set(true);
    this.serverErrors.set({});
    this.general.set('');
    if (this.form.invalid || !this.longEnough() || !this.hasDigit() || this.mismatch()) {
      this.form.markAllAsTouched();
      return;
    }
    this.busy.set(true);
    try {
      await this.auth.register(this.form.getRawValue());
      await this.router.navigate(['/verify'], { queryParams: { sent: 1 } });
    } catch (e) {
      const { general, fields } = apiErrors(e);
      this.serverErrors.set(fields);
      this.general.set(general);
    } finally {
      this.busy.set(false);
    }
  }
}
