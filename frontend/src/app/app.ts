import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from './core/theme.service';
import { NetworkService } from './core/network.service';
import { ConfirmDialogComponent } from './shared/confirm-dialog.component';
import { ToastContainerComponent } from './shared/toast-container.component';

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, ConfirmDialogComponent, ToastContainerComponent],
  template: '<router-outlet /><app-confirm-dialog /><app-toasts />',
})
export class App {
  // Created at start-up so the saved theme applies before the first screen.
  private theme = inject(ThemeService);
  // Watches the connection from the start and announces when it drops.
  private network = inject(NetworkService);
}
