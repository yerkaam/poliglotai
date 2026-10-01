import { HttpClient, HttpContext, HttpParams } from '@angular/common/http';
import { HANDLED_STATUSES } from './error.interceptor';
import { Injectable, inject } from '@angular/core';
import {
  AnswerResult,
  Badge,
  ChatMode,
  ChatSummary,
  ChatUsage,
  CheckResult,
  Conversation,
  CourseStep,
  MyGroup,
  TeacherGroup,
  TeacherGroupDetail,
  Form,
  PlacementQuestion,
  PlacementResult,
  Profile,
  Progress,
  ReviewCheck,
  ReviewQuiz,
  Pronoun,
  Scenario,
  SendResult,
  StepCheckResult,
  StepDetail,
  Tense,
  Today,
  TrainerStats,
  TrainerTask,
  User,
  VerbForms,
  WeekSummary,
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
    return this.http.post<User>('/api/auth/login/', { email, password, remember }, handles(429));
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
  verifyEmail(code: string) {
    return this.http.post<User>('/api/auth/verify-email/', { code });
  }
  resendCode() {
    return this.http.post<{ detail: string; retry_after: number }>('/api/auth/verify-email/resend/', {}, handles(429));
  }
  updateProfile(data: Partial<Profile>) {
    return this.http.patch<User>('/api/auth/profile/', data);
  }
  requestReset(email: string) {
    return this.http.post<{ detail: string; retry_after: number }>('/api/auth/password-reset/', { email }, handles(429));
  }
  changePassword(old_password: string, password: string, password2: string) {
    return this.http.post<{ detail: string }>('/api/auth/password/', { old_password, password, password2 }, handles(429));
  }

  /** Everything stored about the learner, as a JSON file. */
  exportData() {
    return this.http.get('/api/auth/export/', { responseType: 'blob' });
  }

  deleteAccount(password: string) {
    return this.http.post<void>('/api/auth/delete/', { password }, handles(429));
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
  step(number: number) {
    return this.http.get<StepDetail>(`/api/course/${number}/`);
  }
  saveLessons(number: number, done: number) {
    return this.http.post<{ lessons_done: number }>(`/api/course/${number}/lessons/`, { done });
  }
  checkStep(number: number, answers: string[]) {
    return this.http.post<StepCheckResult>(`/api/course/${number}/check/`, { answers });
  }

  // spaced repetition
  today() {
    return this.http.get<Today>('/api/srs/today/');
  }
  answer(wordId: number, answer: 'start' | 'known' | 'remember' | 'forget') {
    return this.http.post<AnswerResult>(`/api/srs/${wordId}/answer/`, { answer });
  }
  /** The server takes the translation the tutor gave in the chat, never one sent from here. */
  /** Checks a review exercise on the server; an empty answer means "I don't know". */
  checkReview(wordId: number, mode: ReviewQuiz['mode'], answer: string) {
    return this.http.post<ReviewCheck>(`/api/srs/${wordId}/check/`, { mode, answer });
  }
  addWord(word: string) {
    return this.http.post<{ word_id: number; word: string; added: boolean }>('/api/srs/add/', { word });
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
  placement() {
    return this.http.get<{ questions: PlacementQuestion[] }>('/api/placement/');
  }
  submitPlacement(answers: string[]) {
    return this.http.post<PlacementResult>('/api/placement/', { answers });
  }
  // teacher's cabinet
  teacherGroups() {
    return this.http.get<TeacherGroup[]>('/api/teacher/groups/');
  }
  createGroup(name: string) {
    return this.http.post<TeacherGroup>('/api/teacher/groups/', { name });
  }
  teacherGroup(id: number) {
    return this.http.get<TeacherGroupDetail>(`/api/teacher/groups/${id}/`);
  }
  deleteGroup(id: number) {
    return this.http.delete<void>(`/api/teacher/groups/${id}/`);
  }
  newGroupCode(id: number) {
    return this.http.post<TeacherGroup>(`/api/teacher/groups/${id}/code/`, {});
  }
  removeStudent(groupId: number, studentId: number) {
    return this.http.delete<void>(`/api/teacher/groups/${groupId}/students/${studentId}/`);
  }

  // the learner's groups
  myGroups() {
    return this.http.get<MyGroup[]>('/api/groups/');
  }
  joinGroup(code: string) {
    return this.http.post<MyGroup>('/api/groups/join/', { code }, handles(429));
  }
  leaveGroup(id: number) {
    return this.http.delete<void>(`/api/groups/${id}/`);
  }

  week() {
    return this.http.get<WeekSummary>('/api/progress/week/');
  }
  achievements() {
    return this.http.get<Badge[]>('/api/achievements/');
  }
  achievementsSeen() {
    return this.http.post<void>('/api/achievements/seen/', {});
  }
  resetProgress() {
    return this.http.post<void>('/api/progress/reset/', { confirm: true });
  }

  // AI chat
  scenarios() {
    return this.http.get<{ scenarios: Scenario[]; usage: ChatUsage }>('/api/chat/scenarios/');
  }
  startConversation(mode: ChatMode, scenario?: string) {
    return this.http.post<Conversation>('/api/chat/conversations/', { mode, scenario: scenario ?? null }, handles(429, 503));
  }
  conversation(id: number) {
    return this.http.get<Conversation>(`/api/chat/conversations/${id}/`);
  }
  send(id: number, text: string) {
    return this.http.post<SendResult>(`/api/chat/conversations/${id}/messages/`, { text }, handles(429, 503));
  }
  summary(id: number) {
    return this.http.get<ChatSummary>(`/api/chat/conversations/${id}/summary/`);
  }
}

/** The screen shows its own message for these statuses (a countdown, "AI unavailable"), so no pop-up. */
function handles(...statuses: number[]) {
  return { context: new HttpContext().set(HANDLED_STATUSES, statuses) };
}
