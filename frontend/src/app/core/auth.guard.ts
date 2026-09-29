import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** AUTH-14: private pages send a logged-out visitor to the login screen. */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isLoggedIn()) return true;
  return router.createUrlTree(['/login'], { queryParams: state.url !== '/' ? { next: state.url } : {} });
};

/** AUTH-04: after registration the learner first sets up the profile. */
export const onboardedGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.user()?.profile.onboarded ? true : inject(Router).createUrlTree(['/onboarding']);
};

/** Login and registration are only for logged-out visitors. */
export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.isLoggedIn() ? inject(Router).createUrlTree(['/']) : true;
};
