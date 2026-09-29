import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Part } from '../core/models';

/** Renders a sentence with auxiliaries, endings and irregular forms in colour (TBL-07). */
@Component({
  selector: 'app-sentence',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `@for (part of parts(); track $index) {<span [class]="'part-' + part.kind">{{ part.text }}</span>}`,
})
export class SentenceComponent {
  readonly parts = input.required<Part[]>();
}
