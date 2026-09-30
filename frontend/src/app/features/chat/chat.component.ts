import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnInit,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { FORM_KK, TENSE_KK } from '../../core/labels';
import { ChatMessage, ChatMode, ChatSummary, ChatUsage, Conversation, Correction, NewWord, Scenario } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { SpeechService } from '../../core/speech.service';
import { ToastService } from '../../core/toast.service';
import { IconComponent } from '../../shared/icon.component';
import { apiErrors } from '../auth/errors';
import { GuardedPage } from '../../core/leave.guard';

const ACTIVE_KEY = 'poliglot-chat';

@Component({
  selector: 'app-chat',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, RouterLink],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent extends GuardedPage implements OnInit {
  private api = inject(ApiService);
  protected speech = inject(SpeechService);
  private store = inject(ProgressStore);
  private toasts = inject(ToastService);
  private feed = viewChild<ElementRef<HTMLElement>>('feed');
  private inputRef = viewChild<ElementRef<HTMLInputElement>>('chatInput');

  protected scenarios = signal<Scenario[]>([]);
  protected usage = signal<ChatUsage>({ used: 0, limit: 30 });
  protected mode = signal<ChatMode>('dialog');
  protected scenario = signal('cafe');
  protected conversation = signal<Conversation | null>(null);
  protected summary = signal<ChatSummary | null>(null);
  protected text = signal('');
  protected sending = signal(false);
  protected starting = signal(false);
  protected error = signal('');
  protected showKk = signal(true);
  protected showSummary = signal(false);
  protected added = signal<Set<string>>(new Set());

  protected modes: { key: ChatMode; label: string }[] = [
    { key: 'dialog', label: $localize`Диалог` },
    { key: 'builder', label: $localize`Құрастырғыш` },
    { key: 'free', label: $localize`Еркін` },
  ];

  protected messages = computed(() => this.conversation()?.messages ?? []);
  protected lastAssistant = computed(() => [...this.messages()].reverse().find((m) => m.role === 'assistant') ?? null);
  protected turn = computed(() => this.messages().filter((m) => m.role === 'assistant').length);
  protected limitReached = computed(() => this.usage().used >= this.usage().limit);
  protected title = computed(() => {
    const c = this.conversation();
    if (!c) return $localize`AI-әңгімелесуші`;
    if (c.mode === 'dialog' && c.scenario) return $localize`«${c.scenario.title_kk}:scenario:» диалогы`;
    return c.mode === 'builder' ? $localize`Фраза құрастырғыш` : $localize`Еркін әңгіме`;
  });

  hasUnsavedWork() {
    const c = this.conversation();
    const inDialog = !!c && !c.finished && c.messages.some((m) => m.role === 'user');
    return !!this.text().trim() || this.sending() || inDialog;
  }

  override leaveTitle() {
    return $localize`Диалогтан шығасыз ба?`;
  }

  override leaveMessage() {
    return this.text().trim()
      ? $localize`Жазылған хабарлама жіберілмейді.`
      : $localize`Диалог аяқталмады. Кейін осы беттен жалғастыра аласыз.`;
  }

  async ngOnInit() {
    try {
      const { scenarios, usage } = await firstValueFrom(this.api.scenarios());
      this.scenarios.set(scenarios);
      this.usage.set(usage);
    } catch (e) {
      this.error.set(apiErrors(e).general);
    }
    const saved = this.readActive();
    if (saved) {
      try {
        this.setConversation(await firstValueFrom(this.api.conversation(saved)));
        this.loadSummary();
      } catch {
        this.writeActive(null);
      }
    }
  }

  protected async start() {
    this.starting.set(true);
    this.error.set('');
    try {
      const conversation = await firstValueFrom(
        this.api.startConversation(this.mode(), this.mode() === 'dialog' ? this.scenario() : undefined),
      );
      this.setConversation(conversation);
      this.summary.set(null);
      this.added.set(new Set());
      this.speakMessage(conversation.messages[0]);
      queueMicrotask(() => this.inputRef()?.nativeElement.focus());
    } catch (e) {
      this.error.set(apiErrors(e).general);
    } finally {
      this.starting.set(false);
    }
  }

  protected newSession() {
    this.conversation.set(null);
    this.summary.set(null);
    this.writeActive(null);
  }

  protected pickScenario(slug: string) {
    this.mode.set('dialog');
    this.scenario.set(slug);
    if (this.conversation()) this.newSession();
  }

  protected pickMode(mode: ChatMode) {
    this.mode.set(mode);
    if (this.conversation() && this.conversation()!.mode !== mode) this.newSession();
  }

  protected async send(event?: Event) {
    event?.preventDefault();
    const conversation = this.conversation();
    const text = this.text().trim();
    if (!conversation || !text || this.sending()) return;
    this.sending.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.api.send(conversation.id, text));
      this.conversation.set({
        ...conversation,
        finished: res.finished,
        messages: [...conversation.messages, res.user_message, res.assistant_message],
      });
      this.usage.set(res.usage);
      this.text.set('');
      this.speakMessage(res.assistant_message);
      this.scrollDown();
      this.loadSummary();
      this.store.refresh();
    } catch (e) {
      if (e instanceof HttpErrorResponse && e.status === 429) {
        this.error.set($localize`Бүгінгі хабарламалар лимиті бітті. Ертең жалғастырамыз!`);
        this.usage.update((u) => ({ ...u, used: u.limit }));
      } else {
        this.error.set(apiErrors(e).general);
      }
    } finally {
      this.sending.set(false);
      queueMicrotask(() => this.inputRef()?.nativeElement.focus());
    }
  }

  protected useTemplate(template: string) {
    this.text.set(template.replace(/…$/, '').trimEnd() + ' ');
    this.inputRef()?.nativeElement.focus();
  }

  protected async addWord(word: NewWord, quiet = false) {
    try {
      await firstValueFrom(this.api.addWord(word.word, word.translation_kk));
      this.added.update((s) => new Set(s).add(word.word.toLowerCase()));
      this.store.refresh();
      if (!quiet) this.toasts.success($localize`«${word.word}:word:» карточкаларға қосылды.`);
      return true;
    } catch (e) {
      this.error.set(apiErrors(e).general);
      return false;
    }
  }

  protected async addAll() {
    let count = 0;
    for (const w of this.summary()?.new_words ?? []) {
      if (!this.isAdded(w) && (await this.addWord(w, true))) count++;
    }
    if (count) this.toasts.success($localize`${count}:count: сөз карточкаларға қосылды.`);
    this.loadSummary();
  }

  protected isAdded(word: NewWord & { added?: boolean }) {
    return !!word.added || this.added().has(word.word.toLowerCase());
  }

  protected cellLabel(c: Correction) {
    return [c.tense ? TENSE_KK[c.tense] : '', c.form ? FORM_KK[c.form] : ''].filter(Boolean).join(' · ');
  }

  /** Each error links to its table cell (or the verb) so the learner can see the rule. */
  protected cellParams(c: Correction) {
    const params: Record<string, string> = {};
    if (c.verb) params['verb'] = c.verb;
    if (c.pronoun) params['pronoun'] = c.pronoun;
    if (c.tense) params['tense'] = c.tense;
    if (c.form) params['form'] = c.form;
    return params;
  }

  protected speakMessage(message: ChatMessage | undefined) {
    if (message?.role === 'assistant') this.speech.speak(message.text);
  }

  private setConversation(conversation: Conversation) {
    this.conversation.set(conversation);
    this.mode.set(conversation.mode);
    if (conversation.scenario) this.scenario.set(conversation.scenario.slug);
    this.writeActive(conversation.id);
    this.scrollDown();
  }

  private loadSummary() {
    const conversation = this.conversation();
    if (!conversation) return;
    this.api.summary(conversation.id).subscribe({
      next: (s) => {
        this.summary.set(s);
        this.usage.set(s.usage);
      },
      error: () => undefined,
    });
  }

  private scrollDown() {
    setTimeout(() => {
      const el = this.feed()?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  private readActive(): number | null {
    try {
      const v = sessionStorage.getItem(ACTIVE_KEY);
      return v ? Number(v) : null;
    } catch {
      return null;
    }
  }

  private writeActive(id: number | null) {
    try {
      if (id) sessionStorage.setItem(ACTIVE_KEY, String(id));
      else sessionStorage.removeItem(ACTIVE_KEY);
    } catch {
      /* storage may be blocked */
    }
  }
}
