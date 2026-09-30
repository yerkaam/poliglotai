import { Injectable, computed, signal } from '@angular/core';

export type Theme = 'light' | 'dark' | 'system';
const KEY = 'poliglot-theme';

/** Light and dark themes; "system" follows the device setting. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<Theme>(this.read());
  private systemDark = signal(false);
  /** The theme actually shown — the toggle icon and label follow it. */
  readonly isDark = computed(() => this.theme() === 'dark' || (this.theme() === 'system' && this.systemDark()));

  constructor() {
    if (typeof matchMedia !== 'undefined') {
      const media = matchMedia('(prefers-color-scheme: dark)');
      this.systemDark.set(media.matches);
      media.addEventListener('change', () => this.systemDark.set(media.matches));
    }
    this.apply(this.theme());
  }

  toggle() {
    this.set(this.isDark() ? 'light' : 'dark');
  }

  set(theme: Theme) {
    this.theme.set(theme);
    this.apply(theme);
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      /* storage may be blocked */
    }
  }

  private apply(theme: Theme) {
    const root = document.documentElement;
    if (theme === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', theme);
  }

  private read(): Theme {
    try {
      const saved = localStorage.getItem(KEY);
      return saved === 'light' || saved === 'dark' ? saved : 'system';
    } catch {
      return 'system';
    }
  }
}
