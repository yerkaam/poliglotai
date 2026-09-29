import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import {
  AnswerResult,
  ChatMode,
  ChatSummary,
  ChatUsage,
  CheckResult,
  Conversation,
  CourseStep,
  Form,
  Profile,
  Progress,
  Pronoun,
  Scenario,
  SendResult,
  Tense,
  Today,
  TrainerStats,
  TrainerTask,
  User,
  VerbForms,
  Word,
} from './models';

/** Typed access to the Django REST API. Cookies carry the session; nothing is stored in JS. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  // auth
  csrf() {
    return this.http.get<{ ok: boolean }>('/api/auth/csrf/');
  }
  me() {
    return this.http.get<User>('/api/auth/me/');
  }
  login(email: string, password: string, remember: boolean) {
    return this.http.post<User>('/api/auth/login/', { email, password, remember });
  }
  register(data: { name: string; email: string; password: string; password2: string; accept_terms: boolean }) {
    return this.http.post<User>('/api/auth/register/', data);
  }
  logout() {
    return this.http.post<void>('/api/auth/logout/', {});
  }
  refresh() {
    return this.http.post<{ ok: boolean }>('/api/auth/refresh/', {});
  }
  updateProfile(data: Partial<Profile>) {
    return this.http.patch<User>('/api/auth/profile/', data);
  }
  requestReset(email: string) {
    return this.http.post<{ detail: string; retry_after: number }>('/api/auth/password-reset/', { email });
  }
  confirmReset(uid: string, token: string, password: string) {
    return this.http.post<{ detail: string }>('/api/auth/password-reset/confirm/', { uid, token, password });
  }

  // verbs and course
  verbs() {
    return this.http.get<Word[]>('/api/verbs/');
  }
  forms(verbId: number, pronoun: Pronoun) {
    return this.http.get<VerbForms>(`/api/verbs/${verbId}/forms/`, { params: new HttpParams().set('pronoun', pronoun) });
  }
  course() {
    return this.http.get<CourseStep[]>('/api/course/');
  }

  // spaced repetition
  today() {
    return this.http.get<Today>('/api/srs/today/');
  }
  answer(wordId: number, answer: 'start' | 'known' | 'remember' | 'forget') {
    return this.http.post<AnswerResult>(`/api/srs/${wordId}/answer/`, { answer });
  }
  addWord(word: string, translation_kk: string, example_en = '') {
    return this.http.post<{ word_id: number; word: string; added: boolean }>('/api/srs/add/', {
      word,
      translation_kk,
      example_en,
    });
  }

  // trainer
  trainerTask() {
    return this.http.get<{ task: TrainerTask; stats: TrainerStats }>('/api/trainer/task/');
  }
  check(data: { verb_id: number; pronoun: Pronoun; tense: Tense; form: Form; answer: string }) {
    return this.http.post<CheckResult>('/api/trainer/check/', data);
  }

  // progress
  progress() {
    return this.http.get<Progress>('/api/progress/');
  }
  resetProgress() {
    return this.http.post<void>('/api/progress/reset/', { confirm: true });
  }

  // AI chat
  scenarios() {
    return this.http.get<{ scenarios: Scenario[]; usage: ChatUsage }>('/api/chat/scenarios/');
  }
  startConversation(mode: ChatMode, scenario?: string) {
    return this.http.post<Conversation>('/api/chat/conversations/', { mode, scenario: scenario ?? null });
  }
  conversation(id: number) {
    return this.http.get<Conversation>(`/api/chat/conversations/${id}/`);
  }
  send(id: number, text: string) {
    return this.http.post<SendResult>(`/api/chat/conversations/${id}/messages/`, { text });
  }
  summary(id: number) {
    return this.http.get<ChatSummary>(`/api/chat/conversations/${id}/summary/`);
  }
}
