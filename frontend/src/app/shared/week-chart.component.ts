import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';
import { WeekDay } from '../core/models';

/**
 * Exercises per day for the last 7 days: one series of columns, so no legend (the title names it).
 * Hover or focus a day for its breakdown; the same numbers are in the table view.
 */
@Component({
  selector: 'app-week-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="chart" role="group" [attr.aria-label]="label()">
      <div class="plot">
        <div class="grid" aria-hidden="true">
          @for (t of ticks(); track t) {
            <div class="tick" [style.bottom.%]="(100 * t) / top()">
              <span>{{ t }}</span>
            </div>
          }
        </div>
        <div class="cols">
          @for (d of days(); track d.date; let i = $index) {
            <button
              type="button"
              class="col"
              [class.active]="hover() === i"
              [attr.aria-label]="describe(d)"
              (mouseenter)="hover.set(i)"
              (mouseleave)="hover.set(null)"
              (focus)="hover.set(i)"
              (blur)="hover.set(null)"
            >
              @if (d.total === max() && d.total > 0) {
                <span class="value" [style.bottom.%]="(100 * d.total) / top()">{{ d.total }}</span>
              }
              <span class="bar" [class.empty]="!d.total" [style.height.%]="(100 * d.total) / top()"></span>
              @if (hover() === i) {
                <span class="tip" role="tooltip" [class.right]="i > 4" [class.left]="i < 2">
                  <b>{{ d.weekday_kk }}, {{ dayMonth(d.date) }}</b>
                  <span class="row"><span i18n>Барлығы</span><b>{{ d.total }}</b></span>
                  <span class="row"><span i18n>Қайталау</span><b>{{ d.reviews }}</b></span>
                  <span class="row"><span i18n>Жаңа сөздер</span><b>{{ d.new_words }}</b></span>
                  <span class="row"><span i18n>Жаттықтырғыш</span><b>{{ d.trainer }}</b></span>
                  <span class="row"><span i18n>AI-чат</span><b>{{ d.chat }}</b></span>
                </span>
              }
            </button>
          }
        </div>
      </div>
      <div class="axis" aria-hidden="true">
        @for (d of days(); track d.date) {
          <span [class.today]="$last">{{ d.weekday_kk }}</span>
        }
      </div>
    </div>

    <details class="table-view">
      <summary i18n>Кесте түрінде</summary>
      <table>
        <thead>
          <tr>
            <th scope="col" i18n>Күн</th>
            <th scope="col" i18n>Қайталау</th>
            <th scope="col" i18n>Жаңа</th>
            <th scope="col" i18n>Сөйлем</th>
            <th scope="col" i18n>Чат</th>
            <th scope="col" i18n>Барлығы</th>
          </tr>
        </thead>
        <tbody>
          @for (d of days(); track d.date) {
            <tr>
              <th scope="row">{{ d.weekday_kk }}, {{ dayMonth(d.date) }}</th>
              <td>{{ d.reviews }}</td>
              <td>{{ d.new_words }}</td>
              <td>{{ d.trainer }}</td>
              <td>{{ d.chat }}</td>
              <td><b>{{ d.total }}</b></td>
            </tr>
          }
        </tbody>
      </table>
    </details>
  `,
  styles: `
    :host { display: block; }
    .chart { --plot-h: 180px; }
    .plot { position: relative; height: var(--plot-h); margin-left: 28px; }
    .grid { position: absolute; inset: 0; pointer-events: none; }
    .tick { position: absolute; left: 0; right: 0; border-top: 1px solid var(--line); }
    .tick span { position: absolute; left: -28px; top: -8px; width: 22px; text-align: right;
      font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }
    .cols { position: absolute; inset: 0; display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
    .col { position: relative; height: 100%; border: 0; padding: 0; background: none; cursor: default;
      display: flex; align-items: flex-end; justify-content: center; border-radius: var(--r-sm); }
    .col:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
    .col.active { background: color-mix(in srgb, var(--ink) 4%, transparent); }
    .bar { width: min(24px, 60%); min-height: 2px; background: var(--red); border-radius: 4px 4px 0 0; }
    .bar.empty { background: var(--line); }
    .value { position: absolute; left: 0; right: 0; margin-bottom: 4px; text-align: center; font-size: 12px;
      font-weight: 700; color: var(--ink); transform: translateY(-100%); padding-bottom: 2px; }
    .axis { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); margin: 6px 0 0 28px;
      font-size: 12px; color: var(--muted); text-align: center; }
    .axis .today { color: var(--ink); font-weight: 700; }
    .tip { position: absolute; bottom: calc(100% - 8px); z-index: 2; min-width: 150px; padding: 10px 12px;
      border-radius: var(--r-sm); background: var(--surface); border: 1px solid var(--line); box-shadow: var(--shadow);
      display: flex; flex-direction: column; gap: 3px; font-size: 13px; text-align: left; color: var(--ink);
      left: 50%; transform: translateX(-50%); pointer-events: none; }
    .tip.left { left: 0; transform: none; }
    .tip.right { left: auto; right: 0; transform: none; }
    .tip .row { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); }
    .tip .row b { color: var(--ink); font-variant-numeric: tabular-nums; }
    .table-view { margin-top: 12px; font-size: 14px; }
    .table-view summary { cursor: pointer; color: var(--muted); min-height: 32px; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; font-variant-numeric: tabular-nums; }
    th, td { padding: 6px 4px; text-align: right; border-bottom: 1px solid var(--line); font-weight: 400; }
    th[scope='row'], thead th:first-child { text-align: left; }
    thead th { color: var(--muted); font-size: 12px; }
  `,
})
export class WeekChartComponent {
  readonly days = input.required<WeekDay[]>();
  protected hover = signal<number | null>(null);

  protected max = computed(() => Math.max(0, ...this.days().map((d) => d.total)));
  /** A clean top for the axis: 0 / half / top, rounded to a step that reads well. */
  protected top = computed(() => {
    const max = Math.max(4, this.max());
    const step = max <= 10 ? 2 : max <= 50 ? 10 : max <= 100 ? 20 : 50;
    return Math.ceil(max / step) * step;
  });
  protected ticks = computed(() => [0, this.top() / 2, this.top()]);
  protected label = computed(
    () => $localize`Соңғы 7 күндегі жаттығулар: ${this.days().map((d) => `${d.weekday_kk} ${d.total}`).join(', ')}:days:`,
  );

  protected dayMonth(iso: string) {
    const [, m, d] = iso.split('-');
    return `${Number(d)}.${m}`;
  }

  protected describe(d: WeekDay) {
    return $localize`${d.weekday_kk}:day:: ${d.total}:total: жаттығу`;
  }
}
