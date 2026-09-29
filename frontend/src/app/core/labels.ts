import { Form, Pronoun, Tense } from './models';

export const PRONOUNS: Pronoun[] = ['I', 'you', 'we', 'they', 'he', 'she'];
export const TENSES: Tense[] = ['future', 'present', 'past'];
export const FORMS: Form[] = ['question', 'affirmative', 'negative'];

export const PRONOUN_KK: Record<Pronoun, string> = {
  I: $localize`мен`,
  you: $localize`сен / сіз`,
  we: $localize`біз`,
  they: $localize`олар`,
  he: $localize`ол (ер)`,
  she: $localize`ол (әйел)`,
};

export const TENSE_KK: Record<Tense, string> = {
  future: $localize`Келер шақ`,
  present: $localize`Осы шақ`,
  past: $localize`Өткен шақ`,
};

export const TENSE_AUX: Record<Tense, string> = {
  future: 'will',
  present: 'do / does',
  past: 'did',
};

export const FORM_KK: Record<Form, string> = {
  question: $localize`сұрақ`,
  affirmative: $localize`болымды`,
  negative: $localize`болымсыз`,
};

export const FORM_SIGN: Record<Form, string> = { question: '?', affirmative: '+', negative: '−' };

/** TBL-09: one short rule per tense, in Kazakh. */
export const TENSE_RULE_KK: Record<Tense, string> = {
  future: $localize`Келер шақ: will + етістік барлық жақта бірдей. Сұрақта will алға шығады, болымсызда won't (= will not).`,
  present: $localize`Осы шақ: he, she үшін етістікке -s / -es қосылады (have → has). Сұрақ пен болымсызда do / does, don't / doesn't; онда -s жоқ.`,
  past: $localize`Өткен шақ: болымдыда етістікке -ed қосылады, бұрыс етістіктің өз формасы бар (buy → bought). Сұрақ пен болымсызда did / didn't + бастапқы форма.`,
};

export const STATUS_KK = {
  new: $localize`жаңа`,
  learning: $localize`үйреніп жатырсыз`,
  learned: $localize`үйренілді`,
  known: $localize`білесіз`,
};

export const INTERVAL_LABELS = [1, 2, 4, 7, 14, 30];

export function capitalize(text: string) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
