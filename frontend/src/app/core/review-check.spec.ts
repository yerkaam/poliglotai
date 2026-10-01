import { Word } from './models';
import { localVerdict } from './review-check';

/** The phone's verdict must match the server's (backend/srs/quiz.py), or offline stages would drift. */
describe('localVerdict', () => {
  const word = (w: string, kk: string, stage: number) => ({ id: 1, word: w, translation_kk: kk, stage }) as Word;

  it('checks the chosen translation and the heard word exactly', () => {
    expect(localVerdict(word('buy', 'сатып алу', 1), 'choice', 'сатып алу').correct).toBeTrue();
    expect(localVerdict(word('buy', 'сатып алу', 1), 'choice', 'ішу').right).toBe('сатып алу');
    expect(localVerdict(word('speak', 'сөйлеу', 3), 'listen', 'Speak').correct).toBeTrue();
    expect(localVerdict(word('speak', 'сөйлеу', 3), 'listen', 'spend').correct).toBeFalse();
  });

  it('forgives one typo in a word of five letters or more, like the server', () => {
    const v = localVerdict(word('study', 'оқу', 5), 'type', 'studdy');
    expect(v.correct && v.almost).toBeTrue();
    expect(localVerdict(word('study', 'оқу', 5), 'type', ' Study! ').almost).toBeFalse();
    expect(localVerdict(word('go', 'бару', 5), 'type', 'do').correct).toBeFalse();
  });

  it('moves the stage the way the server will', () => {
    expect(localVerdict(word('buy', 'сатып алу', 2), 'choice', 'сатып алу').stage).toBe(3);
    const wrong = localVerdict(word('buy', 'сатып алу', 3), 'choice', 'x');
    expect([wrong.stage, wrong.again_today]).toEqual([2, true]);
    expect(localVerdict(word('buy', 'сатып алу', 1), 'type', '').stage).toBe(1);
  });
});
