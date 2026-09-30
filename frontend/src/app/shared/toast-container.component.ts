import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ToastService } from '../core/toast.service';
import { IconComponent } from './icon.component';

@Component({
  selector: 'app-toasts',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  template: `
    <!-- Errors interrupt screen readers (assertive); the rest wait their turn (polite). -->
    <div class="stack" aria-live="assertive" aria-atomic="false">
      @for (t of toastService.toasts(); track t.id) {
        @if (t.kind === 'error') {
          <div class="toast error" role="alert">
            <app-icon name="alert" [size]="20" />
            <span class="text">{{ t.text }}</span>
            <button type="button" class="close" (click)="toastService.dismiss(t.id)" [attr.aria-label]="closeLabel">
              <app-icon name="close" [size]="16" />
            </button>
          </div>
        }
      }
    </div>
    <div class="stack polite" aria-live="polite">
      @for (t of toastService.toasts(); track t.id) {
        @if (t.kind !== 'error') {
          <div class="toast" [class.success]="t.kind === 'success'" role="status">
            <app-icon [name]="t.kind === 'success' ? 'check' : 'refresh'" [size]="20" [class.spin]="t.sticky" />
            <span class="text">{{ t.text }}</span>
            <button type="button" class="close" (click)="toastService.dismiss(t.id)" [attr.aria-label]="closeLabel">
              <app-icon name="close" [size]="16" />
            </button>
          </div>
        }
      }
    </div>
  `,
  styles: `
    :host { position: fixed; z-index: 1000; right: 16px; left: 16px; bottom: calc(92px + env(safe-area-inset-bottom));
      display: flex; flex-direction: column; gap: 8px; pointer-events: none; align-items: center; }
    @media (min-width: 1024px) { :host { left: auto; bottom: 24px; right: 24px; align-items: flex-end; } }
    .stack { display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 420px; }
    .toast { pointer-events: auto; display: flex; align-items: flex-start; gap: 10px; padding: 12px 8px 12px 14px;
      border-radius: var(--r-md); background: var(--ink); color: var(--surface); font-size: 15px; line-height: 1.4;
      box-shadow: 0 12px 32px rgba(26, 20, 20, 0.25); animation: rise 0.2s ease-out; }
    .toast.error { background: var(--red); color: #fff; }
    .toast.success { background: var(--green); color: #fff; }
    .text { flex: 1; padding-top: 1px; }
    .close { border: 0; background: none; color: inherit; opacity: 0.8; width: 32px; height: 32px; margin: -6px 0;
      display: flex; align-items: center; justify-content: center; border-radius: 16px; flex-shrink: 0; }
    .close:hover { opacity: 1; background: rgba(255, 255, 255, 0.15); }
    .spin { animation: spin 1.2s linear infinite; }
    @keyframes rise { from { transform: translateY(8px); opacity: 0; } }
    @keyframes spin { to { transform: rotate(360deg); } }
    @media (prefers-reduced-motion: reduce) { .toast, .spin { animation: none; } }
  `,
})
export class ToastContainerComponent {
  protected toastService = inject(ToastService);
  protected closeLabel = $localize`Жабу`;
}
