import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** The 3×3 mark (the verb table) with the centre cell in red, plus the wordmark. */
@Component({
  selector: 'app-logo',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="mark" [class.inverse]="inverse()" aria-hidden="true">
      @for (i of cells; track i) {
        <span [class.hot]="i === 4"></span>
      }
    </span>
    @if (!compact()) {
      <span class="word">Poliglot<span [class.accent]="!inverse()">Ai</span></span>
    }
  `,
  styles: `
    :host { display: inline-flex; align-items: center; gap: 10px; }
    .mark { display: grid; grid-template-columns: repeat(3, 7px); gap: 2px; }
    .mark span { width: 7px; height: 7px; border-radius: 2px; background: var(--ink); }
    .mark span.hot { background: var(--red); }
    .mark.inverse span { background: #fff; }
    .mark.inverse span.hot { background: #1a1414; }
    .word { font-family: var(--font-display); font-weight: 700; font-size: 19px; letter-spacing: -0.01em; }
    .accent { color: var(--red); }
  `,
})
export class LogoComponent {
  readonly inverse = input(false);
  /** Only the 3×3 mark (collapsed sidebar). */
  readonly compact = input(false);
  protected cells = [0, 1, 2, 3, 4, 5, 6, 7, 8];
}
