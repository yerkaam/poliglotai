import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { IconComponent } from './icon.component';

/** A block that could not load: says so and offers a retry, instead of staying silently empty. */
@Component({
  selector: 'app-load-error',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  template: `
    <div class="box" role="alert">
      <app-icon name="alert" [size]="20" />
      <span>{{ message() || defaultMessage }}</span>
      <button type="button" class="btn btn-ghost retry" (click)="retry.emit()">
        <app-icon name="refresh" [size]="16" />&ngsp;<ng-container i18n>Қайталау</ng-container>
      </button>
    </div>
  `,
  styles: `
    .box { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 12px; padding: 12px 14px;
      border-radius: var(--r-md); background: var(--tint); color: var(--red-strong); font-size: 15px; }
    span { flex: 1; min-width: 160px; }
    .retry { min-height: 40px; padding: 0 14px; font-size: 14px; color: var(--ink); background: var(--surface); }
  `,
})
export class LoadErrorComponent {
  readonly message = input('');
  readonly retry = output<void>();
  protected defaultMessage = $localize`Жүктеу мүмкін болмады.`;
}
