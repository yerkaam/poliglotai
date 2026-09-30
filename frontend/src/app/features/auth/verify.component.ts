import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterNextRender, inject, signal, viewChild } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { IconComponent } from '../../shared/icon.component';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';
import { GuardedPage } from '../../core/leave.guard';

const RESEND_SECONDS = 60;

/** After registration: the 6-digit code from the email confirms the address. */
@Component({
  selector: 'app-verify',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayoutComponent, IconComponent],
  template: `
    <app-auth-layout>
      <span class="mail-icon"><app-icon name="mail" [size]="28" /></span>
      <div class="intro">
        <h2 class="page-title" i18n>Поштаңызды растаңыз</h2>
        <p class="muted">
          <ng-container i18n>Растау кодын мына поштаға жібердік:</ng-container>&ngsp;<b class="email">{{ auth.user()?.email }}</b>.
          <ng-container i18n>Код 10 минут жарамды.</ng-container>
        </p>
      </div>

      @if (error()) {
        <div class="alert" role="alert"><app-icon name="alert" /><span>{{ error() }}</span></div>
      }

      <form class="form" (submit)="submit($event)" novalidate>
        <div class="field">
          <label for="emailCode" i18n>6 таңбалы код</label>
          <input
            #codeInput
            id="emailCode"
            name="code"
            class="input code"
            type="text"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            placeholder="••••••"
            [value]="code()"
            [attr.aria-invalid]="!!error() || null"
            (input)="onInput($event)"
          />
        </div>
        <button type="submit" class="btn btn-primary btn-lg" [disabled]="busy() || code().length !== 6" i18n>Растау</button>
      </form>

      <div class="resend">
        <span class="muted" i18n>Хат келмеді ме? Спам қалтасын тексеріңіз.</span>
        <button type="button" class="link" [disabled]="countdown() > 0 || resending()" (click)="resend()">
          @if (countdown() > 0) {
            <ng-container i18n>Қайта жіберу · 0:{{ pad(countdown()) }}</ng-container>
          } @else {
            <ng-container i18n>Кодты қайта жіберу</ng-container>
          }
        </button>
      </div>
      <p class="foot muted">
        <ng-container i18n>Пошта қате ме?</ng-container>&ngsp;<button type="button" class="link" (click)="auth.logout()" i18n>
          Басқа поштамен тіркелу
        </button>
      </p>
    </app-auth-layout>
  `,
  styleUrl: './auth.scss',
  styles: `
    .mail-icon { width: 56px; height: 56px; border-radius: 18px; background: var(--tint); color: var(--red-strong);
      display: flex; align-items: center; justify-content: center; }
    .email { color: var(--ink); overflow-wrap: anywhere; }
    .code { height: 64px; font-family: var(--font-mono); font-size: 30px; letter-spacing: 0.5em; text-align: center; }
    .resend { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; font-size: 14px; }
    .link { border: 0; background: none; padding: 0; min-height: 44px; color: var(--red); font-weight: 600; font-size: 15px; }
    .link:disabled { color: var(--muted); cursor: default; }
  `,
})
export class VerifyComponent extends GuardedPage {
  protected auth = inject(AuthService);
  private api = inject(ApiService);
  private router = inject(Router);
  private toasts = inject(ToastService);
  private codeInput = viewChild<ElementRef<HTMLInputElement>>('codeInput');

  protected code = signal('');
  protected busy = signal(false);
  protected resending = signal(false);
  protected error = signal('');
  protected countdown = signal(0);
  private timer: ReturnType<typeof setInterval> | undefined;

  constructor() {
    super();
    inject(DestroyRef).onDestroy(() => clearInterval(this.timer));
    // Right after registration the code has just been sent: resending waits 60 seconds.
    if (inject(ActivatedRoute).snapshot.queryParamMap.get('sent')) this.startCountdown(RESEND_SECONDS);
    afterNextRender(() => this.codeInput()?.nativeElement.focus());
  }

  hasUnsavedWork() {
    return this.code().length > 0 && !this.busy();
  }

  override leaveMessage() {
    return $localize`Пошта әлі расталмады. Кодты кейін енгізуге болады.`;
  }

  protected pad(n: number) {
    return String(n).padStart(2, '0');
  }

  protected onInput(event: Event) {
    const input = event.target as HTMLInputElement;
    const digits = input.value.replace(/\D/g, '').slice(0, 6);
    input.value = digits;
    this.code.set(digits);
    this.error.set('');
    if (digits.length === 6) this.submit();
  }

  async submit(event?: Event) {
    event?.preventDefault();
    if (this.code().length !== 6 || this.busy()) return;
    this.busy.set(true);
    try {
      await this.auth.verifyEmail(this.code());
      const onboarded = this.auth.user()?.profile.onboarded;
      await this.router.navigate([onboarded ? '/' : '/onboarding']);
    } catch (e) {
      this.error.set(apiErrors(e).general || apiErrors(e).fields['code'] || '');
      this.code.set('');
      const input = this.codeInput()?.nativeElement;
      if (input) {
        input.value = '';
        input.focus();
      }
    } finally {
      this.busy.set(false);
    }
  }

  async resend() {
    this.resending.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.api.resendCode());
      this.toasts.success($localize`Жаңа код жіберілді. Поштаңызды тексеріңіз.`);
      this.startCountdown(res.retry_after);
    } catch (e) {
      if (e instanceof HttpErrorResponse && e.status === 429) this.startCountdown(e.error?.retry_after ?? RESEND_SECONDS);
      else this.error.set(apiErrors(e).general);
    } finally {
      this.resending.set(false);
    }
  }

  private startCountdown(seconds: number) {
    clearInterval(this.timer);
    this.countdown.set(seconds);
    this.timer = setInterval(() => {
      this.countdown.update((s) => Math.max(0, s - 1));
      if (this.countdown() === 0) clearInterval(this.timer);
    }, 1000);
  }
}
