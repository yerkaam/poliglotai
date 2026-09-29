import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark' | 'system';
const KEY = 'poliglot-theme';

/** Light and dark themes; "system" follows the device setting. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<Theme>(this.read());

  constructor() {
    this.apply(this.theme());
  }

  toggle() {
    const isDark =
      this.theme() === 'dark' ||
      (this.theme() === 'system' && window.matchMedia?.('(prefers-color-scheme: dark)').matches);
    this.set(isDark ? 'light' : 'dark');
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
