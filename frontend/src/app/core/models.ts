export type Level = 'A0' | 'A1';
export type Pronoun = 'I' | 'you' | 'we' | 'they' | 'he' | 'she';
export type Tense = 'future' | 'present' | 'past';
export type Form = 'question' | 'affirmative' | 'negative';
export type WordStatus = 'new' | 'learning' | 'learned' | 'known';

export interface Profile {
  level: Level;
  daily_new_limit: 5 | 10 | 15 | 20;
  daily_minutes: number;
  onboarded: boolean;
}

export interface User {
  id: number;
  email: string;
  name: string;
  profile: Profile;
}

export interface Word {
  id: number;
  word: string;
  translation_kk: string;
  ipa: string;
  is_verb: boolean;
  past: string;
  is_irregular: boolean;
  example_en: string;
  example_kk: string;
  topic: string;
  course_step: number | null;
  status: WordStatus;
  stage: number;
}

export interface Part {
  text: string;
  kind: 'plain' | 'aux' | 'ending' | 'irregular';
}

export interface Cell {
  tense: Tense;
  form: Form;
  text: string;
  parts: Part[];
}

export interface VerbForms {
  verb: Word;
  pronoun: Pronoun;
  cells: Cell[];
}

export interface Today {
  review: Word[];
  new: Word[];
  new_limit: number;
  new_left: number;
  intervals: number[];
}

export interface AnswerResult {
  word_id: number;
  status: WordStatus;
  stage: number;
  next_review_date: string | null;
  again_today: boolean;
}

export interface GoalTask {
  key: 'reviews' | 'new' | 'trainer' | 'chat';
  target: number;
  done: number;
  complete: boolean;
  scenario?: string;
}

export interface Progress {
  stats: { learning: number; learned: number; due: number; accuracy: number | null; streak: number };
  stages: { stage: number; count: number }[];
  not_started: number;
  learned_of: { learned: number; total: number };
  goal: { tasks: GoalTask[]; done: number; total: number };
}

export interface TrainerStats {
  total: number;
  correct: number;
  accuracy: number | null;
  streak: number;
}

export interface TrainerTask {
  verb: { id: number; word: string; translation_kk: string };
  pronoun: Pronoun;
  pronoun_kk: string;
  tense: Tense;
  tense_kk: string;
  form: Form;
  form_kk: string;
  from_learning: boolean;
}

export interface CheckResult {
  correct: boolean;
  expected: string;
  parts: Part[];
  stats: TrainerStats;
}

export interface CourseStep {
  number: number;
  title_kk: string;
  title_en: string;
  description_kk: string;
  status: 'open' | 'soon';
  words_total: number;
  words_learned: number;
  percent: number;
}

export type ChatMode = 'dialog' | 'builder' | 'free';

export interface Scenario {
  slug: string;
  title_kk: string;
  max_turns: number;
}

export interface Correction {
  wrong: string;
  right: string;
  explanation_kk: string;
  verb: string | null;
  pronoun: Pronoun | null;
  tense: Tense | null;
  form: Form | null;
}

export interface NewWord {
  word: string;
  translation_kk: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  translation_kk: string;
  hint_en: string;
  new_words: NewWord[];
  correct: boolean | null;
  corrections: Correction[];
  created_at: string;
}

export interface Conversation {
  id: number;
  mode: ChatMode;
  scenario: Scenario | null;
  finished: boolean;
  created_at: string;
  messages: ChatMessage[];
}

export interface ChatUsage {
  used: number;
  limit: number;
}

export interface SendResult {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  finished: boolean;
  off_topic: boolean;
  usage: ChatUsage;
}

export interface ChatSummary {
  written: number;
  correct: number;
  top_errors: (Correction & { count: number; cell_label_kk: string })[];
  new_words: (NewWord & { added: boolean })[];
  usage: ChatUsage;
}
