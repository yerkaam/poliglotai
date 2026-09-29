import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { IconComponent } from '../../shared/icon.component';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';

@Component({
  selector: 'app-reset',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, IconComponent],
  template: `
    <app-auth-layout>
      <a routerLink="/login" class="back" i18n-aria-label aria-label="Артқа"><app-icon name="back" /></a>
      <div class="intro">
        <h2 class="page-title" i18n>Құпиясөзді қалпына келтіру</h2>
        <p class="muted" i18n>Электрондық поштаңызды енгізіңіз. Жаңа құпиясөз орнату сілтемесін жібереміз.</p>
      </div>

      <form [formGroup]="form" (ngSubmit)="submit()" class="form" novalidate>
        <div class="field">
          <label for="resetEmail" i18n>Электрондық пошта</label>
          <input id="resetEmail" class="input" type="email" formControlName="email" autocomplete="email"
                 placeholder="name@mail.kz" [attr.aria-invalid]="!!error() || null" />
        </div>
        @if (error()) { <span class="field-error" role="alert">{{ error() }}</span> }
        <button type="submit" class="btn btn-primary btn-lg" [disabled]="busy() || countdown() > 0">
          @if (countdown() > 0) {
            <ng-container i18n>Қайта жіберу · {{ clock() }}</ng-container>
          } @else if (sent()) {
            <ng-container i18n>Қайта жіберу</ng-container>
          } @else {
            <ng-container i18n>Сілтеме жіберу</ng-container>
          }
        </button>
      </form>

      @if (sent()) {
        <div class="alert alert-ok" role="status">
          <app-icon name="mail" />
          <div>
            <b i18n>Хат жіберілді</b><br />
            <span i18n>Егер бұл пошта тіркелген болса, 5 минут ішінде сілтеме келеді. Спам қалтасын да тексеріңіз.</span>
          </div>
        </div>
      }
      <p class="foot"><a routerLink="/login" i18n>Кіру бетіне оралу</a></p>
    </app-auth-layout>
  `,
  styleUrl: './auth.scss',
})
export class ResetComponent {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);

  protected form = this.fb.nonNullable.group({ email: ['', [Validators.required, Validators.email]] });
  protected busy = signal(false);
  protected sent = signal(false);
  protected error = signal('');
  protected countdown = signal(0);
  private timer: ReturnType<typeof setInterval> | undefined;

  constructor() {
    inject(DestroyRef).onDestroy(() => clearInterval(this.timer));
  }

  protected clock() {
    const s = this.countdown();
    return `0:${String(s).padStart(2, '0')}`;
  }

  async submit() {
    if (this.form.invalid) {
      this.error.set($localize`Дұрыс пошта енгізіңіз.`);
      return;
    }
    this.busy.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.api.requestReset(this.form.getRawValue().email));
      this.sent.set(true);
      this.startCountdown(res.retry_after);
    } catch (e) {
      if (e instanceof HttpErrorResponse && e.status === 429) {
        this.startCountdown(e.error?.retry_after ?? 60);
      } else {
        this.error.set(apiErrors(e).general);
      }
    } finally {
      this.busy.set(false);
    }
  }

  /** AUTH-12: the letter can be sent again only after 60 seconds. */
  private startCountdown(seconds: number) {
    clearInterval(this.timer);
    this.countdown.set(seconds);
    this.timer = setInterval(() => {
      this.countdown.update((s) => Math.max(0, s - 1));
      if (this.countdown() === 0) clearInterval(this.timer);
    }, 1000);
  }
}
