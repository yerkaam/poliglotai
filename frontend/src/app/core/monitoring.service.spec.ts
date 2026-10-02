import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { MonitoringService, withoutQuery } from './monitoring.service';

describe('MonitoringService', () => {
  it('drops query strings and fragments from reported addresses', () => {
    expect(withoutQuery('/reset-password?token=abc&email=a@b.kz')).toBe('/reset-password');
    expect(withoutQuery('/chat#end')).toBe('/chat');
    expect(withoutQuery(undefined)).toBeUndefined();
  });

  it('stays off and keeps nothing when the server gives no DSN', async () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient()] });
    const service = TestBed.inject(MonitoringService);
    spyOn(window, 'fetch').and.resolveTo(
      new Response(JSON.stringify({ sentry_dsn: '', environment: 'test', release: '' })),
    );
    service.report(new Error('before start'));
    await service.init();
    service.report(new Error('after start'));
    expect((service as unknown as { early: unknown[] }).early).toEqual([]);
    expect((service as unknown as { sentry: unknown }).sentry).toBeNull();
  });

  it('survives a failed config request', async () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient()] });
    const service = TestBed.inject(MonitoringService);
    spyOn(window, 'fetch').and.rejectWith(new TypeError('offline'));
    await expectAsync(service.init()).toBeResolved();
  });
});
