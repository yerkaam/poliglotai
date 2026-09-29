import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { FORM_KK, FORM_SIGN, FORMS, TENSE_AUX, TENSE_KK, TENSES } from '../core/labels';
import { Cell, Form, Tense } from '../core/models';
import { SpeechService } from '../core/speech.service';
import { SentenceComponent } from './sentence.component';

/**
 * The 3×3 table: rows future / present / past, columns question / affirmative / negative.
 * Tapping a cell reads the sentence aloud (TBL-08). On narrow screens it becomes three stacked
 * rows of three, so it fits 360 px without horizontal scrolling.
 */
@Component({
  selector: 'app-verb-grid',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [SentenceComponent],
  template: `
    <div class="grid" [class.compact]="compact()" role="table" i18n-aria-label aria-label="Етістік кестесі">
      <div class="head" role="row">
        <span role="columnheader" class="corner"></span>
        @for (form of forms; track form) {
          <span role="columnheader" class="col-head"><b>{{ sign[form] }}</b> {{ formKk[form] }}</span>
        }
      </div>
      @for (tense of tenses; track tense) {
        <div class="row" role="row">
          <span role="rowheader" class="row-head">
            {{ tenseKk[tense] }}<small>{{ aux[tense] }}</small>
          </span>
          @for (cell of rowCells(tense); track cell.form) {
            <div role="cell">
            <button
              type="button"
              class="cell"
              [class.focus]="isFocus(cell.tense, cell.form)"
              [class.playing]="speech.speaking() === cell.text"
              [attr.aria-label]="cell.text + ' — ' + tenseKk[cell.tense] + ', ' + formKk[cell.form]"
              (click)="speech.speak(cell.text)"
            >
              <app-sentence [parts]="cell.parts" />
            </button>
            </div>
          }
        </div>
      }
    </div>
  `,
  styleUrl: './verb-grid.component.scss',
})
export class VerbGridComponent {
  protected speech = inject(SpeechService);
  readonly cells = input.required<Cell[]>();
  readonly focusTense = input<Tense | null>(null);
  readonly focusForm = input<Form | null>(null);
  readonly compact = input(false);

  protected tenses = TENSES;
  protected forms = FORMS;
  protected tenseKk = TENSE_KK;
  protected formKk = FORM_KK;
  protected sign = FORM_SIGN;
  protected aux = TENSE_AUX;

  private byTense = computed(() => {
    const map = new Map<Tense, Cell[]>();
    for (const cell of this.cells()) map.set(cell.tense, [...(map.get(cell.tense) ?? []), cell]);
    return map;
  });

  protected rowCells(tense: Tense) {
    return this.byTense().get(tense) ?? [];
  }

  protected isFocus(tense: Tense, form: Form) {
    return this.focusTense() === tense && this.focusForm() === form;
  }
}
