import { TestBed } from '@angular/core/testing';
import { Cell } from '../core/models';
import { SpeechService } from '../core/speech.service';
import { VerbGridComponent } from './verb-grid.component';

const CELLS: Cell[] = [
  { tense: 'future', form: 'question', text: 'Will she buy?', parts: [{ text: 'Will', kind: 'aux' }, { text: ' she buy?', kind: 'plain' }] },
  { tense: 'future', form: 'affirmative', text: 'She will buy.', parts: [{ text: 'She will buy.', kind: 'plain' }] },
  { tense: 'future', form: 'negative', text: "She won't buy.", parts: [{ text: "She won't buy.", kind: 'plain' }] },
  { tense: 'present', form: 'question', text: 'Does she buy?', parts: [{ text: 'Does she buy?', kind: 'plain' }] },
  { tense: 'present', form: 'affirmative', text: 'She buys.', parts: [{ text: 'She buy', kind: 'plain' }, { text: 's', kind: 'ending' }, { text: '.', kind: 'plain' }] },
  { tense: 'present', form: 'negative', text: "She doesn't buy.", parts: [{ text: "She doesn't buy.", kind: 'plain' }] },
  { tense: 'past', form: 'question', text: 'Did she buy?', parts: [{ text: 'Did she buy?', kind: 'plain' }] },
  { tense: 'past', form: 'affirmative', text: 'She bought.', parts: [{ text: 'She ', kind: 'plain' }, { text: 'bought', kind: 'irregular' }, { text: '.', kind: 'plain' }] },
  { tense: 'past', form: 'negative', text: "She didn't buy.", parts: [{ text: "She didn't buy.", kind: 'plain' }] },
];

describe('VerbGridComponent', () => {
  const speak = jasmine.createSpy('speak');

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [VerbGridComponent],
      providers: [{ provide: SpeechService, useValue: { speak, speaking: () => null } }],
    });
  });

  function render(focus?: { tense: 'past'; form: 'affirmative' }) {
    const fixture = TestBed.createComponent(VerbGridComponent);
    fixture.componentRef.setInput('cells', CELLS);
    if (focus) {
      fixture.componentRef.setInput('focusTense', focus.tense);
      fixture.componentRef.setInput('focusForm', focus.form);
    }
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('shows nine cells in three tense rows', () => {
    const el = render();
    expect(el.querySelectorAll('button.cell').length).toBe(9);
    expect(el.querySelectorAll('[role="row"]').length).toBe(4);
  });

  it('colours auxiliaries, endings and irregular forms', () => {
    const el = render();
    expect(el.querySelector('.part-aux')?.textContent).toBe('Will');
    expect(el.querySelector('.part-ending')?.textContent).toBe('s');
    expect(el.querySelector('.part-irregular')?.textContent).toBe('bought');
  });

  it('highlights the linked cell', () => {
    const el = render({ tense: 'past', form: 'affirmative' });
    expect(el.querySelector('.cell.focus')?.textContent?.trim()).toBe('She bought.');
  });

  it('reads a sentence aloud when its cell is pressed', () => {
    const el = render();
    (el.querySelectorAll('button.cell')[4] as HTMLButtonElement).click();
    expect(speak).toHaveBeenCalledWith('She buys.');
  });
});
