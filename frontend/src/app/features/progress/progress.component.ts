import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { ApiService } from '../../core/api.service';
import { apiResource } from '../../core/api-resource';
import { Badge, WeekSummary } from '../../core/models';
import { IconComponent, IconName } from '../../shared/icon.component';
import { LoadErrorComponent } from '../../shared/load-error.component';
import { WeekChartComponent } from '../../shared/week-chart.component';

/** The week in numbers and the badges. */
@Component({
  selector: 'app-progress',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, LoadErrorComponent, WeekChartComponent],
  template: `
    <div class="page">
      <header class="head">
        <span class="eyebrow" i18n>Соңғы 7 күн</span>
        <h1 class="page-title" i18n>Прогресс</h1>
      </header>

      @if (week.failed()) {
        <section class="card"><app-load-error (retry)="week.reload()" /></section>
      } @else if (week.value(); as w) {
        <section class="tiles" i18n-aria-label aria-label="Апта қорытындысы">
          <div class="card tile">
            <span class="label" i18n>Белсенді күндер</span>
            <b class="value">{{ w.active_days }}<small>/7</small></b>
            @if (w.streak) {
              <span class="delta" i18n>серия: {{ w.streak }} күн</span>
            }
          </div>
          <div class="card tile">
            <span class="label" i18n>Жаттығулар</span>
            <b class="value">{{ w.total }}</b>
            <span class="delta" [class.up]="change() > 0" [class.down]="change() < 0">
              @if (change() > 0) {
                <ng-container i18n>өткен аптадан +{{ change() }}</ng-container>
              } @else if (change() < 0) {
                <ng-container i18n>өткен аптадан {{ change() }}</ng-container>
              } @else {
                <ng-container i18n>өткен аптамен бірдей</ng-container>
              }
            </span>
          </div>
          <div class="card tile">
            <span class="label" i18n>Жаңа сөздер</span>
            <b class="value">{{ w.new_words }}</b>
            <span class="delta" i18n>қайталау: {{ w.reviews }}</span>
          </div>
          <div class="card tile">
            <span class="label" i18n>Дәлдік</span>
            <b class="value">{{ w.accuracy !== null ? w.accuracy + '%' : '–' }}</b>
            <span class="delta" i18n>{{ w.sentences }} сөйлем</span>
          </div>
        </section>

        <section class="card" aria-labelledby="chartTitle">
          <h2 id="chartTitle" class="section-title" i18n>Күн сайынғы жаттығулар</h2>
          <p class="muted small" i18n>Қайталау, жаңа сөздер, жаттықтырғыш сөйлемдері және AI-чат хабарламалары</p>
          <app-week-chart [days]="w.days" />
        </section>
      } @else {
        <div class="spinner" role="status"><span class="visually-hidden" i18n>Жүктелуде</span></div>
      }

      <section class="card" aria-labelledby="badgesTitle">
        <div class="badges-head">
          <h2 id="badgesTitle" class="section-title" i18n>Жетістіктер</h2>
          @if (badges.value().length) {
            <span class="muted small" i18n>{{ earned() }} / {{ badges.value().length }}</span>
          }
        </div>
        @if (badges.failed()) {
          <app-load-error (retry)="badges.reload()" />
        }
        <ul class="badges">
          @for (b of badges.value(); track b.key) {
            <li [class.earned]="!!b.unlocked_at">
              <span class="badge-icon" aria-hidden="true"><app-icon [name]="icon(b)" [size]="22" /></span>
              <span class="badge-text">
                <b>{{ b.title_kk }}</b>
                <small class="muted">{{ b.description_kk }}</small>
                @if (!b.unlocked_at) {
                  <span class="meter" role="progressbar" [attr.aria-valuenow]="b.current" aria-valuemin="0"
                        [attr.aria-valuemax]="b.target" [attr.aria-label]="b.title_kk">
                    <span [style.width.%]="(100 * b.current) / b.target"></span>
                  </span>
                  <small class="muted count">{{ b.current }} / {{ b.target }}</small>
                } @else {
                  <span class="visually-hidden" i18n>алынды</span>
                }
              </span>
            </li>
          }
        </ul>
      </section>
    </div>
  `,
  styles: `
    .page { display: flex; flex-direction: column; gap: 16px; }
    .head { display: flex; flex-direction: column; gap: 6px; }
    .section-title { font-size: 17px; margin: 0 0 4px; }
    .small { font-size: 13px; margin: 0 0 14px; }
    .tiles { display: grid; gap: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    @container main (min-width: 760px) { .tiles { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
    .tile { display: flex; flex-direction: column; gap: 2px; padding: 14px 16px; }
    .label { font-size: 13px; color: var(--muted); }
    .value { font-size: 28px; font-weight: 700; font-variant-numeric: tabular-nums; }
    .value small { font-size: 15px; color: var(--muted); font-weight: 600; }
    .delta { font-size: 13px; color: var(--muted); }
    .delta.up { color: var(--green); }
    .badges-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .badges { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
    .badges li { display: flex; gap: 12px; align-items: flex-start; padding: 12px; border-radius: var(--r-md);
      border: 1px solid var(--line); }
    .badges li.earned { background: var(--tint); border-color: transparent; }
    .badge-icon { flex: none; width: 40px; height: 40px; border-radius: 20px; display: flex; align-items: center;
      justify-content: center; background: var(--bg); color: var(--muted); }
    .earned .badge-icon { background: var(--red); color: var(--on-red); }
    .badge-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
    .badge-text b { font-size: 15px; }
    li:not(.earned) .badge-text b { color: var(--muted); }
    .meter { margin-top: 6px; height: 6px; border-radius: 3px; background: var(--line); overflow: hidden; }
    .meter span { display: block; height: 100%; background: var(--red); border-radius: 3px; }
    .count { font-variant-numeric: tabular-nums; }
  `,
})
export class ProgressComponent {
  private api = inject(ApiService);
  protected week = apiResource(() => this.api.week(), null as WeekSummary | null);
  protected badges = apiResource(() => this.api.achievements(), [] as Badge[]);
  protected change = computed(() => {
    const w = this.week.value();
    return w ? w.total - w.previous_total : 0;
  });
  protected earned = computed(() => this.badges.value().filter((b) => b.unlocked_at).length);

  protected icon(b: Badge): IconName {
    return (b.unlocked_at ? b.icon : 'trophy') as IconName;
  }
}
