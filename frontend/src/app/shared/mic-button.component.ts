import { ChangeDetectionStrategy, Component, inject, input, output, signal } from '@angular/core';
import { SpeechInputError, SpeechInputService } from '../core/speech-input.service';
import { ToastService } from '../core/toast.service';
import { IconComponent } from './icon.component';

const NOTICE_KEY = 'poliglot-mic-notice';

/**
 * "Say it" button: tap, speak one English sentence, the text arrives in (heard). Tap again to stop.
 * Hidden where the browser cannot recognise speech.
 */
@Component({
  selector: 'app-mic-button',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  template: `
    @if (speech.supported) {
      <button
        type="button"
        class="mic"
        [class.on]="mine()"
        [disabled]="disabled()"
        [attr.aria-pressed]="mine()"
        [attr.aria-label]="mine() ? stopLabel : label() || startLabel"
        [attr.title]="mine() ? stopLabel : label() || startLabel"
        (click)="toggle()"
      >
        <app-icon name="mic" [size]="size()" />
      </button>
    }
  `,
  styles: `
    :host { display: contents; }
    .mic { flex: none; width: 48px; height: 48px; border-radius: 24px; border: 1.5px solid var(--line);
      background: var(--surface); color: var(--ink); display: flex; align-items: center; justify-content: center; }
    .mic:hover:not(:disabled) { border-color: var(--ink); }
    .mic:disabled { opacity: 0.5; }
    .mic.on { background: var(--red); border-color: var(--red); color: var(--on-red);
      animation: pulse 1.2s ease-in-out infinite; }
    @keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(215, 38, 46, 0.45); }
      50% { box-shadow: 0 0 0 10px rgba(215, 38, 46, 0); } }
    @media (prefers-reduced-motion: reduce) { .mic.on { animation: none; } }
  `,
})
export class MicButtonComponent {
  protected speech = inject(SpeechInputService);
  private toasts = inject(ToastService);

  readonly disabled = input(false);
  readonly size = input(22);
  /** What the button does here; "answer by voice" when not given. */
  readonly label = input('');
  /** The final sentence heard ('' is never emitted). */
  readonly heard = output<string>();
  /** The text heard so far, while the learner speaks. */
  readonly partial = output<string>();

  /** This button (not another one on the page) is listening. */
  protected mine = signal(false);
  protected startLabel = $localize`Айтып жауап беру`;
  protected stopLabel = $localize`Тыңдауды тоқтату`;

  protected async toggle() {
    if (this.mine()) {
      this.speech.stop();
      return;
    }
    this.showNoticeOnce();
    this.mine.set(true);
    try {
      const text = await this.speech.listen({ onPartial: (t) => this.partial.emit(t) });
      if (text) this.heard.emit(text);
      else this.toasts.info($localize`Ештеңе естілмеді. Микрофонға жақынырақ, анық айтып көріңіз.`);
    } catch (error) {
      this.toasts.error(this.message(error as SpeechInputError));
    } finally {
      this.mine.set(false);
    }
  }

  private message(error: SpeechInputError): string {
    switch (error) {
      case 'denied':
        return $localize`Микрофонға рұқсат жоқ. Браузер баптауларында осы сайтқа микрофонды ашыңыз.`;
      case 'no-speech':
        return $localize`Ештеңе естілмеді. Микрофонға жақынырақ, анық айтып көріңіз.`;
      case 'network':
        return $localize`Сөйлеуді тану үшін интернет керек. Байланысты тексеріңіз.`;
      default:
        return $localize`Сөйлеуді тану мүмкін болмады. Жауапты жазып жіберіңіз.`;
    }
  }

  /** Browsers send the audio to their own recognition service: say so once. */
  private showNoticeOnce() {
    try {
      if (localStorage.getItem(NOTICE_KEY)) return;
      localStorage.setItem(NOTICE_KEY, '1');
    } catch {
      return;
    }
    this.toasts.info(
      $localize`Айтқаныңызды браузердің сөйлеу тану қызметі мәтінге айналдырады. Біз дыбысты сақтамаймыз.`,
    );
  }
}
