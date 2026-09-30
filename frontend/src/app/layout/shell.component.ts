import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../core/auth.service';
import { ConfirmService } from '../core/confirm.service';
import { ProgressStore } from '../core/progress.store';
import { ThemeService } from '../core/theme.service';
import { IconComponent, IconName } from '../shared/icon.component';
import { LogoComponent } from '../shared/logo.component';

interface NavItem {
  path: string;
  label: string;
  short: string;
  icon: IconName;
}

const SIDEBAR_KEY = 'poliglot-sidebar';
/** Below this width the sidebar starts as a narrow icon rail, so pages keep room for two columns. */
const WIDE = '(min-width: 1280px)';

@Component({
  selector: 'app-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent, LogoComponent],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
})
export class ShellComponent {
  protected auth = inject(AuthService);
  protected store = inject(ProgressStore);
  protected theme = inject(ThemeService);
  private confirm = inject(ConfirmService);
  private router = inject(Router);
  private topbar = viewChild<ElementRef<HTMLElement>>('topbar');

  protected nav: NavItem[] = [
    { path: '/', label: $localize`Басты бет`, short: $localize`Басты бет`, icon: 'home' },
    { path: '/table', label: $localize`Етістік кестесі`, short: $localize`Кесте`, icon: 'grid' },
    { path: '/words', label: $localize`Сөздер`, short: $localize`Сөздер`, icon: 'cards' },
    { path: '/trainer', label: $localize`Жаттықтырғыш`, short: $localize`Жаттығу`, icon: 'target' },
    { path: '/chat', label: $localize`AI-чат`, short: $localize`AI-чат`, icon: 'chat' },
    { path: '/course', label: $localize`Курс · 16 қадам`, short: $localize`Курс`, icon: 'book' },
  ];

  protected stats = computed(() => this.store.progress()?.stats ?? null);
  protected learnedOf = computed(() => this.store.progress()?.learned_of ?? null);
  protected initial = computed(() => (this.auth.user()?.name ?? '?').trim().charAt(0).toUpperCase());
  protected themeLabel = computed(() => (this.theme.isDark() ? $localize`Жарық тақырып` : $localize`Қараңғы тақырып`));
  protected collapseLabel = $localize`Мәзірді жию`;
  protected expandLabel = $localize`Мәзірді ашу`;

  /** The learner's own choice wins; without one the rail follows the window width. */
  private userChoice = signal<boolean | null>(readChoice());
  private wide = signal(typeof matchMedia === 'undefined' || matchMedia(WIDE).matches);
  protected collapsed = computed(() => this.userChoice() ?? !this.wide());

  constructor() {
    // The stats bar refreshes on every screen change, including the first one.
    this.router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.store.refresh());

    const destroyRef = inject(DestroyRef);
    if (typeof matchMedia !== 'undefined') {
      const media = matchMedia(WIDE);
      const onChange = () => this.wide.set(media.matches);
      media.addEventListener('change', onChange);
      destroyRef.onDestroy(() => media.removeEventListener('change', onChange));
    }

    // Full-height screens (the chat) size themselves from the sticky top bar's height.
    afterNextRender(() => {
      const el = this.topbar()?.nativeElement;
      if (!el || typeof ResizeObserver === 'undefined') return;
      const observer = new ResizeObserver(() =>
        document.documentElement.style.setProperty('--topbar-h', `${el.offsetHeight}px`),
      );
      observer.observe(el);
      destroyRef.onDestroy(() => observer.disconnect());
    });
  }

  protected toggleSidebar() {
    const next = !this.collapsed();
    this.userChoice.set(next);
    try {
      localStorage.setItem(SIDEBAR_KEY, next ? 'rail' : 'full');
    } catch {
      /* storage may be blocked */
    }
  }

  /** Logging out always asks first; the leave guards of the current screen do not ask a second time. */
  protected async logout() {
    const ok = await this.confirm.ask({
      title: $localize`Аккаунттан шығасыз ба?`,
      message: $localize`Прогресс сақталған. Қайта кіру үшін пошта мен құпиясөз керек болады.`,
      confirmText: $localize`Шығу`,
      cancelText: $localize`Қалу`,
    });
    if (!ok) return;
    this.confirm.bypassLeaveGuards = true;
    try {
      this.store.clear();
      await this.auth.logout();
    } finally {
      this.confirm.bypassLeaveGuards = false;
    }
  }
}

function readChoice(): boolean | null {
  try {
    const saved = localStorage.getItem(SIDEBAR_KEY);
    return saved === 'rail' ? true : saved === 'full' ? false : null;
  } catch {
    return null;
  }
}
