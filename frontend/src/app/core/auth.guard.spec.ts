import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { authGuard, onboardedGuard, verifiedGuard } from './auth.guard';
import { AuthService } from './auth.service';
import { User } from './models';

describe('auth guards', () => {
  const user = signal<User | null>(null);

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { user, isLoggedIn: () => user() !== null } },
      ],
    });
  });

  const run = (guard: typeof authGuard, url = '/words') =>
    TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
    );

  it('sends a logged-out visitor to login with the page to return to', () => {
    user.set(null);
    const result = run(authGuard) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(result)).toBe('/login?next=%2Fwords');
  });

  it('sends a learner without a profile to onboarding', () => {
    user.set({ id: 1, is_teacher: false, email: 'a@b.kz', name: 'A', email_verified: true, profile: { level: 'A0', daily_new_limit: 10, daily_minutes: 15, onboarded: false, reminder_enabled: true, reminder_hour: 19 } });
    expect(run(authGuard)).toBeTrue();
    expect(TestBed.inject(Router).serializeUrl(run(onboardedGuard) as UrlTree)).toBe('/onboarding');
  });

  it('sends a learner with an unconfirmed email to the code screen', () => {
    user.set({ id: 1, is_teacher: false, email: 'a@b.kz', name: 'A', email_verified: false, profile: { level: 'A0', daily_new_limit: 10, daily_minutes: 15, onboarded: true, reminder_enabled: true, reminder_hour: 19 } });
    expect(TestBed.inject(Router).serializeUrl(run(verifiedGuard) as UrlTree)).toBe('/verify');
  });
});
