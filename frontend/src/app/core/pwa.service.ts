import { Injectable, computed, inject, signal } from '@angular/core';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { filter } from 'rxjs';
import { ConfirmService } from './confirm.service';

interface InstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

/** Installing the app on the phone, and offering a new version once it has downloaded. */
@Injectable({ providedIn: 'root' })
export class PwaService {
  private updates = inject(SwUpdate);
  private confirm = inject(ConfirmService);
  private promptEvent = signal<InstallPromptEvent | null>(null);

  readonly installed = signal(
    typeof matchMedia !== 'undefined' &&
      (matchMedia('(display-mode: standalone)').matches ||
        (navigator as unknown as { standalone?: boolean }).standalone === true),
  );
  /** Chrome / Edge / Android: the browser can show its own install dialog. */
  readonly canInstall = computed(() => !this.installed() && this.promptEvent() !== null);
  /** iPhone / iPad Safari has no install dialog: the screen explains "Share → Add to Home Screen". */
  readonly iosHint = computed(
    () => !this.installed() && typeof navigator !== 'undefined' && /iphone|ipad|ipod/i.test(navigator.userAgent),
  );

  /** Called once at start-up. */
  init() {
    if (typeof window === 'undefined') return;
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault(); // keep it for our own button instead of the browser's mini-bar
      this.promptEvent.set(event as InstallPromptEvent);
    });
    window.addEventListener('appinstalled', () => {
      this.installed.set(true);
      this.promptEvent.set(null);
    });
    if (this.updates.isEnabled) {
      this.updates.versionUpdates
        .pipe(filter((e): e is VersionReadyEvent => e.type === 'VERSION_READY'))
        .subscribe(() => this.offerReload());
    }
  }

  async install(): Promise<boolean> {
    const event = this.promptEvent();
    if (!event) return false;
    await event.prompt();
    const { outcome } = await event.userChoice;
    this.promptEvent.set(null);
    return outcome === 'accepted';
  }

  private async offerReload() {
    const ok = await this.confirm.ask({
      title: $localize`Жаңа нұсқа дайын`,
      message: $localize`PoliglotAi жаңартылды. Бетті қазір жаңартсаңыз, жаңа мүмкіндіктер ашылады.`,
      confirmText: $localize`Жаңарту`,
      cancelText: $localize`Кейін`,
    });
    if (ok) document.location.reload();
  }
}

/** Data the service worker kept for offline use: removed on logout so the next person sees nothing of it. */
export async function clearOfflineData() {
  if (typeof caches === 'undefined') return;
  const names = await caches.keys();
  await Promise.all(names.filter((n) => n.includes(':data:')).map((n) => caches.delete(n)));
}
