import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { User } from './models';
import { OfflineQueueService } from './offline-queue.service';
import { ProgressStore } from './progress.store';

describe('OfflineQueueService', () => {
  const user = signal<User | null>(null);
  let sent: number[];

  beforeEach(() => {
    localStorage.removeItem('poliglot-offline-answers');
    sent = [];
    user.set({ id: 1 } as User);
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { user } },
        { provide: ProgressStore, useValue: { refresh: () => undefined } },
        {
          provide: ApiService,
          useValue: {
            answer: (wordId: number) => {
              sent.push(wordId);
              return of({});
            },
            checkReview: (wordId: number) => {
              sent.push(wordId);
              return of({});
            },
          },
        },
      ],
    });
  });

  afterEach(() => localStorage.removeItem('poliglot-offline-answers'));

  it("sends a learner's offline answers only to that learner's account", async () => {
    const queue = TestBed.inject(OfflineQueueService);
    let online = false;
    spyOnProperty(navigator, 'onLine').and.callFake(() => online);
    queue.add({ kind: 'answer', wordId: 10, answer: 'start' });

    // Learner 1 logs out offline; learner 2 logs in on the same phone and the connection is back.
    user.set({ id: 2 } as User);
    expect(queue.pendingWordIds().size).toBe(0);
    online = true;
    await queue.flush();
    expect(sent).toEqual([]);

    // Learner 1 comes back: now the answer goes.
    user.set({ id: 1 } as User);
    await queue.flush();
    expect(sent).toEqual([10]);
    expect(queue.pending()).toEqual([]);
  });
});
