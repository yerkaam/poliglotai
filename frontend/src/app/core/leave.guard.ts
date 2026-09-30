import { Directive, HostListener, inject } from '@angular/core';
import { CanDeactivateFn } from '@angular/router';
import { ConfirmService } from './confirm.service';

/**
 * A screen with work that would be lost on leaving (a started session, a half-filled form).
 * The route guard asks before an in-app navigation; the browser asks before closing or reloading the tab.
 */
@Directive()
export abstract class GuardedPage {
  /** True while leaving would lose something the learner did. */
  abstract hasUnsavedWork(): boolean;

  leaveTitle(): string {
    return $localize`Шынымен шығасыз ба?`;
  }

  leaveMessage(): string {
    return $localize`Енгізілген деректер сақталмайды.`;
  }

  @HostListener('window:beforeunload', ['$event'])
  protected warnBeforeUnload(event: BeforeUnloadEvent) {
    if (this.hasUnsavedWork()) {
      event.preventDefault();
      event.returnValue = '';
    }
  }
}

export const leaveGuard: CanDeactivateFn<GuardedPage> = (page) => {
  const confirm = inject(ConfirmService);
  if (confirm.bypassLeaveGuards || !page?.hasUnsavedWork()) return true;
  return confirm.ask({ title: page.leaveTitle(), message: page.leaveMessage() });
};
