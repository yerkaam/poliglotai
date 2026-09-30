import { ChangeDetectionStrategy, Component, ElementRef, effect, inject, viewChild } from '@angular/core';
import { ConfirmService } from '../core/confirm.service';

@Component({
  selector: 'app-confirm-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <dialog #dialog class="dialog" aria-labelledby="confirmTitle" aria-describedby="confirmMessage" (cancel)="onCancel($event)">
      @if (confirm.pending(); as p) {
        <h2 id="confirmTitle">{{ p.title }}</h2>
        <p id="confirmMessage" class="muted">{{ p.message }}</p>
        <div class="actions">
          <button type="button" class="btn btn-ghost" (click)="confirm.answer(false)">{{ p.cancelText ?? stay }}</button>
          <button type="button" class="btn btn-primary" (click)="confirm.answer(true)">{{ p.confirmText ?? leave }}</button>
        </div>
      }
    </dialog>
  `,
  styles: `
    .dialog { border: 0; border-radius: var(--r-lg); padding: 24px; max-width: 420px; width: calc(100% - 32px);
      background: var(--surface); color: var(--ink); box-shadow: 0 24px 64px rgba(26, 20, 20, 0.25); }
    .dialog::backdrop { background: rgba(26, 20, 20, 0.5); }
    h2 { font-size: 19px; }
    p { margin: 10px 0 20px; }
    .actions { display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }
  `,
})
export class ConfirmDialogComponent {
  protected confirm = inject(ConfirmService);
  private dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');
  protected stay = $localize`Қалу`;
  protected leave = $localize`Шығу`;

  constructor() {
    effect(() => {
      const el = this.dialog().nativeElement;
      if (this.confirm.pending() && !el.open) {
        el.showModal();
        // "Stay" is the safe default: Enter or Escape keep the learner where they are.
        queueMicrotask(() => el.querySelector<HTMLButtonElement>('.btn-ghost')?.focus());
      } else if (!this.confirm.pending() && el.open) {
        el.close();
      }
    });
  }

  protected onCancel(event: Event) {
    event.preventDefault();
    this.confirm.answer(false);
  }
}
