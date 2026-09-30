import { HttpErrorResponse } from '@angular/common/http';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { apiErrors } from '../features/auth/errors';
import { ToastService } from './toast.service';

describe('ToastService', () => {
  let toasts: ToastService;
  beforeEach(() => (toasts = TestBed.inject(ToastService)));

  it('shows the same message once, however many times it is reported', () => {
    toasts.error('Серверде қате');
    toasts.error('Серверде қате');
    expect(toasts.toasts().length).toBe(1);
  });

  it('keeps at most three and hides non-sticky ones on their own', fakeAsync(() => {
    ['a', 'b', 'c', 'd'].forEach((t) => toasts.info(t));
    expect(toasts.toasts().map((t) => t.text)).toEqual(['b', 'c', 'd']);
    const sticky = toasts.info('оянып жатыр', { sticky: true });
    tick(10000);
    expect(toasts.toasts().map((t) => t.id)).toEqual([sticky]);
    toasts.dismiss(sticky);
    expect(toasts.toasts()).toEqual([]);
  }));
});

describe('apiErrors', () => {
  it('passes field errors and the general message through', () => {
    const e = new HttpErrorResponse({ status: 400, error: { email: ['Бос'], detail: 'Қате', code: 'invalid' } });
    expect(apiErrors(e)).toEqual({ general: 'Қате', fields: { email: 'Бос' } });
  });
});
