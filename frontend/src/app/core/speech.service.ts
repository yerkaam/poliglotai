import { Injectable, signal } from '@angular/core';

/** MVP voice-over: the browser's speech synthesis, British English. */
@Injectable({ providedIn: 'root' })
export class SpeechService {
  readonly supported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  readonly speaking = signal<string | null>(null);
  private voice: SpeechSynthesisVoice | null = null;

  constructor() {
    if (!this.supported) return;
    const pick = () => {
      const voices = speechSynthesis.getVoices();
      this.voice =
        voices.find((v) => v.lang === 'en-GB' && /female|google/i.test(v.name)) ??
        voices.find((v) => v.lang === 'en-GB') ??
        voices.find((v) => v.lang.startsWith('en')) ??
        null;
    };
    pick();
    speechSynthesis.addEventListener?.('voiceschanged', pick);
  }

  speak(text: string, rate = 0.92) {
    if (!this.supported || !text) return;
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-GB';
    utterance.rate = rate;
    if (this.voice) utterance.voice = this.voice;
    utterance.onend = () => this.speaking.set(null);
    utterance.onerror = () => this.speaking.set(null);
    this.speaking.set(text);
    speechSynthesis.speak(utterance);
  }
}
