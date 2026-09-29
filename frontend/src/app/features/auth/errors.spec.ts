import { HttpErrorResponse } from '@angular/common/http';
import { apiErrors } from './errors';

describe('apiErrors', () => {
  it('splits DRF field errors from the general message', () => {
    const error = new HttpErrorResponse({
      status: 400,
      error: { email: ['Бұл поштамен аккаунт бұрыннан бар.'], detail: 'Қате' },
    });
    expect(apiErrors(error)).toEqual({ general: 'Қате', fields: { email: 'Бұл поштамен аккаунт бұрыннан бар.' } });
  });

  it('falls back to a network message', () => {
    expect(apiErrors(new Error('offline')).general).toContain('Байланыс');
  });
});
