import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { IconComponent } from '../../shared/icon.component';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';
import { PasswordInputComponent } from './password-input.component';

@Component({
  selector: 'app-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, PasswordInputComponent, IconComponent],
  template: `
    <app-auth-layout>
      <div class="segmented" role="group" i18n-aria-label aria-label="Кіру немесе тіркелу">
        <button type="button" aria-pressed="true" i18n>Кіру</button>
        <button type="button" aria-pressed="false" routerLink="/register" i18n>Тіркелу</button>
      </div>

      <div class="intro">
        <h2 class="page-title" i18n>Қош келдіңіз!</h2>
        <p class="muted" i18n>Жалғастыру үшін аккаунтыңызға кіріңіз.</p>
      </div>

      @if (error()) {
        <div class="alert" role="alert">
          <app-icon name="alert" />
          <span><b i18n>Кіру мүмкін болмады.</b> {{ error() }}</span>
        </div>
      }
      @if (notice()) {
        <div class="alert alert-ok" role="status"><app-icon name="check" /><span>{{ notice() }}</span></div>
      }

      <form [formGroup]="form" (ngSubmit)="submit()" class="form" novalidate>
        <div class="field">
          <label for="loginEmail" i18n>Электрондық пошта</label>
          <input id="loginEmail" class="input" type="email" formControlName="email" autocomplete="email"
                 placeholder="name@mail.kz" [attr.aria-invalid]="!!error() || null" />
        </div>
        <div class="field">
          <div class="label-row">
            <label for="loginPassword" i18n>Құпиясөз</label>
            <a routerLink="/reset" i18n>Құпиясөзді ұмыттыңыз ба?</a>
          </div>
          <app-password-input inputId="loginPassword" formControlName="password" [invalid]="!!error()" />
        </div>
        <label class="check">
          <input type="checkbox" formControlName="remember" />
          <span i18n>Мені есте сақта</span>
        </label>
        <button type="submit" class="btn btn-primary btn-lg" [disabled]="busy()" i18n>Кіру</button>
      </form>

      <p class="foot muted">
        <ng-container i18n>Аккаунтыңыз жоқ па?</ng-container>&ngsp;<a routerLink="/register" i18n>Тіркелу</a>
      </p>
    </app-auth-layout>
  `,
  styleUrl: './auth.scss',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  protected busy = signal(false);
  protected error = signal('');
  protected notice = signal(this.route.snapshot.queryParamMap.get('reset') ? $localize`Құпиясөз жаңартылды. Енді кіре аласыз.` : '');

  protected form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
    remember: [true],
  });

  async submit() {
    this.notice.set('');
    if (this.form.invalid) {
      this.error.set($localize`Пошта мен құпиясөзді енгізіңіз.`);
      return;
    }
    this.busy.set(true);
    this.error.set('');
    const { email, password, remember } = this.form.getRawValue();
    try {
      await this.auth.login(email, password, remember);
      const next = this.route.snapshot.queryParamMap.get('next');
      await this.router.navigateByUrl(next && next.startsWith('/') && !next.startsWith('//') ? next : '/');
    } catch (e) {
      // AUTH-06: one general message, never which field is wrong.
      this.error.set(apiErrors(e).general);
    } finally {
      this.busy.set(false);
    }
  }
}
