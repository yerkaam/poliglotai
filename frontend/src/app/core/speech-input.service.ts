import { Injectable, signal } from '@angular/core';

/** The browser's speech recognition (Chrome, Edge, Safari). Firefox has none: the microphone button hides. */
interface Recognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
interface RecognitionEvent {
  resultIndex: number;
  results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>;
}
type RecognitionCtor = new () => Recognition;

export type SpeechInputError = 'denied' | 'no-speech' | 'network' | 'other';

export interface ListenOptions {
  /** Called with the text heard so far, while the learner is still speaking. */
  onPartial?: (text: string) => void;
}

/** One English sentence spoken by the learner, as text. */
@Injectable({ providedIn: 'root' })
export class SpeechInputService {
  private readonly Ctor: RecognitionCtor | undefined =
    typeof window === 'undefined'
      ? undefined
      : ((window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor })
          .SpeechRecognition ??
        (window as unknown as { webkitSpeechRecognition?: RecognitionCtor }).webkitSpeechRecognition);

  readonly supported = !!this.Ctor;
  readonly listening = signal(false);
  private active: Recognition | null = null;

  /**
   * Listens for one sentence and resolves with what was heard ('' if nothing).
   * Rejects with a SpeechInputError the screen can explain.
   */
  listen(options: ListenOptions = {}): Promise<string> {
    if (!this.Ctor) return Promise.reject<string>('other' satisfies SpeechInputError);
    this.stop();
    // Our own voice-over must not be heard as the learner's answer.
    if ('speechSynthesis' in window) speechSynthesis.cancel();

    const recognition = new this.Ctor();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;
    this.active = recognition;
    this.listening.set(true);

    return new Promise<string>((resolve, reject) => {
      let finalText = '';
      let failed: SpeechInputError | null = null;
      recognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) finalText += result[0].transcript;
          else interim += result[0].transcript;
        }
        options.onPartial?.((finalText + interim).trim());
      };
      recognition.onerror = (event) => {
        failed =
          event.error === 'not-allowed' || event.error === 'service-not-allowed'
            ? 'denied'
            : event.error === 'no-speech'
              ? 'no-speech'
              : event.error === 'network'
                ? 'network'
                : event.error === 'aborted'
                  ? null
                  : 'other';
      };
      recognition.onend = () => {
        this.listening.set(false);
        if (this.active === recognition) this.active = null;
        if (failed) reject(failed);
        else resolve(finalText.trim());
      };
      try {
        recognition.start();
      } catch {
        this.listening.set(false);
        reject('other' satisfies SpeechInputError);
      }
    });
  }

  /** Stops listening; what was heard so far is still delivered. */
  stop() {
    this.active?.stop();
  }
}
