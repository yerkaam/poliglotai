import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { IconComponent } from '../../shared/icon.component';
import { AuthLayoutComponent } from './auth-layout.component';
import { apiErrors } from './errors';
import { PasswordInputComponent } from './password-input.component';

@Component({
  selector: 'app-reset-confirm',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, PasswordInputComponent, IconComponent],
  template: `
    <app-auth-layout>
      <div class="intro">
        <h2 class="page-title" i18n>Жаңа құпиясөз</h2>
        <p class="muted" i18n>Жаңа құпиясөзді екі рет енгізіңіз.</p>
      </div>
      @if (error()) {
        <div class="alert" role="alert"><app-icon name="alert" />
          <span>{{ error() }}&ngsp;<a routerLink="/reset" i18n>Жаңа сілтеме сұрау</a></span></div>
      }
      <form [formGroup]="form" (ngSubmit)="submit()" class="form" novalidate>
        <div class="field">
          <label for="newPassword" i18n>Жаңа құпиясөз</label>
          <app-password-input inputId="newPassword" formControlName="password" autocomplete="new-password" describedBy="newRules" />
          <div class="rules" id="newRules" aria-live="polite">
            <span [class.ok]="longEnough()"><app-icon [name]="longEnough() ? 'check' : 'close'" [size]="14" [stroke]="3" />
              <ng-container i18n>Кемінде 8 таңба</ng-container></span>
            <span [class.ok]="hasDigit()"><app-icon [name]="hasDigit() ? 'check' : 'close'" [size]="14" [stroke]="3" />
              <ng-container i18n>Кемінде 1 сан</ng-container></span>
          </div>
        </div>
        <div class="field">
          <label for="newPassword2" i18n>Құпиясөзді қайталаңыз</label>
          <app-password-input inputId="newPassword2" formControlName="password2" autocomplete="new-password" [invalid]="mismatch()" />
          @if (mismatch()) { <span class="field-error" i18n>Құпиясөздер сәйкес емес.</span> }
        </div>
        <button type="submit" class="btn btn-primary btn-lg" [disabled]="busy()" i18n>Сақтау</button>
      </form>
    </app-auth-layout>
  `,
  styleUrl: './auth.scss',
})
export class ResetConfirmComponent {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);
  private router = inject(Router);
  private params = inject(ActivatedRoute).snapshot.queryParamMap;

  protected busy = signal(false);
  protected error = signal('');
  protected form = this.fb.nonNullable.group({
    password: ['', Validators.required],
    password2: ['', Validators.required],
  });
  private value = toSignal(this.form.valueChanges, { initialValue: this.form.getRawValue() });
  protected longEnough = computed(() => (this.value().password ?? '').length >= 8);
  protected hasDigit = computed(() => /\d/.test(this.value().password ?? ''));
  protected mismatch = computed(() => !!this.value().password2 && this.value().password !== this.value().password2);

  async submit() {
    if (!this.longEnough() || !this.hasDigit() || this.mismatch() || this.form.invalid) return;
    this.busy.set(true);
    this.error.set('');
    try {
      await firstValueFrom(
        this.api.confirmReset(this.params.get('uid') ?? '', this.params.get('token') ?? '', this.form.getRawValue().password),
      );
      await this.router.navigate(['/login'], { queryParams: { reset: 1 } });
    } catch (e) {
      const { general, fields } = apiErrors(e);
      this.error.set(general || fields['password'] || Object.values(fields)[0] || '');
    } finally {
      this.busy.set(false);
    }
  }
}
