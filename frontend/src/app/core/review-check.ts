import { ReviewCheck, ReviewQuiz, Word } from './models';

/**
 * The same verdict the server gives (srs/quiz.py), for answers given without internet.
 * The answer is still sent to the server later, which checks it again and moves the word.
 */
export function localVerdict(word: Word, mode: ReviewQuiz['mode'], answer: string): ReviewCheck {
  const given = answer.trim();
  let correct = false;
  let almost = false;
  let right = word.word;
  if (mode === 'choice') {
    right = word.translation_kk;
    correct = given === word.translation_kk;
  } else if (mode === 'listen') {
    correct = given.toLowerCase() === word.word.toLowerCase();
  } else {
    const a = normalize(given);
    const b = normalize(word.word);
    correct = a === b;
    almost = !correct && !!a && b.length >= 5 && distance(a, b) === 1;
    correct = correct || almost;
  }
  const stage = correct ? word.stage + 1 : Math.max(1, word.stage - 1);
  return {
    word_id: word.id,
    correct,
    almost,
    right,
    status: correct && word.stage >= 6 ? 'learned' : 'learning',
    stage: Math.min(stage, 6),
    next_review_date: null,
    again_today: !correct,
  };
}

function normalize(text: string): string {
  return text.toLowerCase().replace(/[’'`]/g, '').replace(/[^a-z ]+/g, ' ').split(/\s+/).filter(Boolean).join(' ');
}

function distance(a: string, b: string): number {
  let previous = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const current = [i];
    for (let j = 1; j <= b.length; j++) {
      current.push(Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    }
    previous = current;
  }
  return previous[b.length];
}
