import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { FORM_SIGN, TENSE_AUX } from '../../core/labels';
import { CheckResult, TrainerStats, TrainerTask } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { SpeechService } from '../../core/speech.service';
import { IconComponent } from '../../shared/icon.component';
import { SentenceComponent } from '../../shared/sentence.component';
import { apiErrors } from '../auth/errors';
import { GuardedPage } from '../../core/leave.guard';

@Component({
  selector: 'app-trainer',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, SentenceComponent, RouterLink],
  templateUrl: './trainer.component.html',
  styleUrl: './trainer.component.scss',
})
export class TrainerComponent extends GuardedPage implements OnInit {
  private api = inject(ApiService);
  private speech = inject(SpeechService);
  private store = inject(ProgressStore);
  private inputRef = viewChild<ElementRef<HTMLInputElement>>('answerInput');

  protected task = signal<TrainerTask | null>(null);
  protected stats = signal<TrainerStats | null>(null);
  protected result = signal<CheckResult | null>(null);
  protected answer = signal('');
  protected busy = signal(false);
  protected error = signal('');
  protected sign = FORM_SIGN;
  protected aux = TENSE_AUX;
  private nextTimer: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    super();
    inject(DestroyRef).onDestroy(() => clearTimeout(this.nextTimer));
  }

  /** Checked sentences are saved on the server; only a typed, unchecked sentence would be lost. */
  hasUnsavedWork() {
    return !!this.answer().trim() && !this.result();
  }

  override leaveTitle() {
    return $localize`Жаттығудан шығасыз ба?`;
  }

  override leaveMessage() {
    return $localize`Жазылған сөйлем тексерілмей қалады.`;
  }

  ngOnInit() {
    this.next();
  }

  private loadingNext = false;

  protected async next() {
    clearTimeout(this.nextTimer);
    // Enter right after a correct answer and the automatic step must not load two tasks.
    if (this.loadingNext) return;
    this.loadingNext = true;
    this.error.set('');
    try {
      const { task, stats } = await firstValueFrom(this.api.trainerTask());
      this.task.set(task);
      this.stats.set(stats);
      this.result.set(null);
      this.answer.set('');
      queueMicrotask(() => this.inputRef()?.nativeElement.focus());
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.loadingNext = false;
    }
  }

  /** Enter checks the sentence; a correct one is read aloud and the next task follows. */
  protected async check(event: Event) {
    event.preventDefault();
    const task = this.task();
    if (!task || this.busy()) return;
    if (this.result()) {
      this.next();
      return;
    }
    if (!this.answer().trim()) return;
    this.busy.set(true);
    try {
      const result = await firstValueFrom(
        this.api.check({
          verb_id: task.verb.id,
          pronoun: task.pronoun,
          tense: task.tense,
          form: task.form,
          answer: this.answer(),
        }),
      );
      this.result.set(result);
      this.stats.set(result.stats);
      this.store.refresh();
      if (result.correct) {
        this.speech.speak(result.expected);
        this.nextTimer = setTimeout(() => this.next(), 1800);
      }
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.busy.set(false);
    }
  }
}
