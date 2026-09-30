import { Routes } from '@angular/router';
import { authGuard, guestGuard, onboardedGuard, unverifiedGuard, verifiedGuard } from './core/auth.guard';
import { ShellComponent } from './layout/shell.component';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    title: $localize`Кіру · PoliglotAi`,
    loadComponent: () => import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    canActivate: [guestGuard],
    title: $localize`Тіркелу · PoliglotAi`,
    loadComponent: () => import('./features/auth/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'reset',
    title: $localize`Құпиясөзді қалпына келтіру · PoliglotAi`,
    loadComponent: () => import('./features/auth/reset.component').then((m) => m.ResetComponent),
  },
  {
    path: 'reset/confirm',
    title: $localize`Жаңа құпиясөз · PoliglotAi`,
    loadComponent: () => import('./features/auth/reset-confirm.component').then((m) => m.ResetConfirmComponent),
  },
  {
    path: 'verify',
    canActivate: [authGuard, unverifiedGuard],
    title: $localize`Поштаны растау · PoliglotAi`,
    loadComponent: () => import('./features/auth/verify.component').then((m) => m.VerifyComponent),
  },
  {
    path: 'onboarding',
    canActivate: [authGuard, verifiedGuard],
    title: $localize`Баптау · PoliglotAi`,
    loadComponent: () => import('./features/auth/onboarding.component').then((m) => m.OnboardingComponent),
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard, verifiedGuard, onboardedGuard],
    children: [
      {
        path: '',
        title: $localize`Басты бет · PoliglotAi`,
        loadComponent: () => import('./features/home/home.component').then((m) => m.HomeComponent),
      },
      {
        path: 'table',
        title: $localize`Етістік кестесі · PoliglotAi`,
        loadComponent: () => import('./features/table/table.component').then((m) => m.TableComponent),
      },
      {
        path: 'words',
        title: $localize`Сөздер · PoliglotAi`,
        loadComponent: () => import('./features/words/words.component').then((m) => m.WordsComponent),
      },
      {
        path: 'trainer',
        title: $localize`Жаттықтырғыш · PoliglotAi`,
        loadComponent: () => import('./features/trainer/trainer.component').then((m) => m.TrainerComponent),
      },
      {
        path: 'chat',
        title: $localize`AI-чат · PoliglotAi`,
        loadComponent: () => import('./features/chat/chat.component').then((m) => m.ChatComponent),
      },
      {
        path: 'course',
        title: $localize`Курс · PoliglotAi`,
        loadComponent: () => import('./features/course/course.component').then((m) => m.CourseComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
