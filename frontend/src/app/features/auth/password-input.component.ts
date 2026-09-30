import { ChangeDetectionStrategy, Component, forwardRef, input, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { IconComponent } from '../../shared/icon.component';

/** Password field with a show / hide button (AUTH-07). */
@Component({
  selector: 'app-password-input',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => PasswordInputComponent), multi: true }],
  template: `
    <div class="wrap">
      <input
        class="input"
        [id]="inputId()"
        [attr.name]="name() || null"
        [type]="visible() ? 'text' : 'password'"
        [attr.autocomplete]="autocomplete()"
        [attr.aria-invalid]="invalid() || null"
        [attr.aria-describedby]="describedBy() || null"
        [value]="value()"
        [disabled]="disabled()"
        (input)="onInput($event)"
        (blur)="onTouched()"
      />
      <button
        type="button"
        class="toggle"
        (click)="visible.set(!visible())"
        [attr.aria-label]="visible() ? hideLabel : showLabel"
        [attr.aria-pressed]="visible()"
      >
        <app-icon [name]="visible() ? 'eyeOff' : 'eye'" />
      </button>
    </div>
  `,
  styles: `
    .wrap { position: relative; }
    .input { padding-right: 52px; }
    .toggle { position: absolute; right: 4px; top: 50%; transform: translateY(-50%); width: 44px; height: 44px;
      border: 0; background: none; display: flex; align-items: center; justify-content: center; color: var(--muted); }
  `,
})
export class PasswordInputComponent implements ControlValueAccessor {
  readonly inputId = input.required<string>();
  /** name + autocomplete let password managers recognise the field */
  readonly name = input('');
  readonly autocomplete = input('current-password');
  readonly invalid = input(false);
  readonly describedBy = input<string>('');

  protected visible = signal(false);
  protected value = signal('');
  protected disabled = signal(false);
  protected showLabel = $localize`Құпиясөзді көрсету`;
  protected hideLabel = $localize`Құпиясөзді жасыру`;

  private onChange: (v: string) => void = () => undefined;
  protected onTouched: () => void = () => undefined;

  protected onInput(event: Event) {
    const v = (event.target as HTMLInputElement).value;
    this.value.set(v);
    this.onChange(v);
  }

  writeValue(v: string | null) {
    this.value.set(v ?? '');
  }
  registerOnChange(fn: (v: string) => void) {
    this.onChange = fn;
  }
  registerOnTouched(fn: () => void) {
    this.onTouched = fn;
  }
  setDisabledState(d: boolean) {
    this.disabled.set(d);
  }
}
