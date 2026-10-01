import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, effect, inject, input, signal, untracked } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { apiResource } from '../../core/api-resource';
import { ConfirmService } from '../../core/confirm.service';
import { TeacherGroup, TeacherGroupDetail } from '../../core/models';
import { ToastService } from '../../core/toast.service';
import { IconComponent } from '../../shared/icon.component';
import { LoadErrorComponent } from '../../shared/load-error.component';
import { apiErrors } from '../auth/errors';

/** The teacher's cabinet: groups, their join codes, each learner's progress and the group's common mistakes. */
@Component({
  selector: 'app-teacher',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, LoadErrorComponent, RouterLink, DatePipe],
  template: `
    <div class="page">
      <header class="head">
        <span class="eyebrow" i18n>Мұғалім кабинеті</span>
        <h1 class="page-title" i18n>Топтар</h1>
      </header>

      <div class="layout">
        <aside class="card groups">
          @if (groups.failed()) {
            <app-load-error (retry)="groups.reload()" />
          }
          <ul>
            @for (g of groups.value(); track g.id) {
              <li>
                <a [routerLink]="[]" [queryParams]="{ group: g.id }" [class.active]="selectedId() === g.id">
                  <b>{{ g.name }}</b>
                  <small class="muted" i18n>{{ g.students }} оқушы</small>
                </a>
              </li>
            } @empty {
              @if (!groups.loading()) {
                <li class="muted empty" i18n>Әзірге топ жоқ. Алғашқысын құрыңыз.</li>
              }
            }
          </ul>
          <form class="create" (submit)="create($event)">
            <label for="groupName" class="visually-hidden" i18n>Жаңа топтың атауы</label>
            <input id="groupName" class="input" maxlength="80" i18n-placeholder placeholder="Мысалы: 7А сынып"
                   [value]="newName()" (input)="newName.set($any($event.target).value)" />
            <button type="submit" class="btn btn-primary" [disabled]="!newName().trim() || busy()" i18n>Топ құру</button>
          </form>
        </aside>

        <section class="detail">
          @if (detailFailed()) {
            <div class="card"><app-load-error (retry)="loadDetail()" /></div>
          } @else if (detail(); as d) {
            <div class="card code-card">
              <div>
                <h2 class="section-title">{{ d.name }}</h2>
                <p class="muted" i18n>Оқушылар «Баптаулар» бетінде осы кодты енгізіп қосылады.</p>
              </div>
              <div class="code-row">
                <span class="code mono" aria-label="Код">{{ d.code }}</span>
                <button type="button" class="btn btn-outline" (click)="copyInvite(d)" i18n>Шақыруды көшіру</button>
                <button type="button" class="btn btn-ghost" (click)="newCode(d)" i18n>Жаңа код</button>
              </div>
            </div>

            <div class="card">
              <h2 class="section-title" i18n>Жиі кездесетін қателер · 30 күн</h2>
              @for (m of d.mistakes; track m.label_kk) {
                <a class="mistake" routerLink="/table" [queryParams]="{ tense: m.tense, form: m.form }">
                  <b>{{ m.label_kk }}</b>
                  <span class="muted" i18n>{{ m.mistakes }} қате · {{ m.learners }} оқушы</span>
                </a>
              } @empty {
                <p class="muted" i18n>Қате әзірге жоқ — жаттықтырғыш пен AI-чаттағы қателер осында жиналады.</p>
              }
            </div>

            <div class="card">
              <h2 class="section-title" i18n>Оқушылар · {{ d.rows.length }}</h2>
              @if (!d.rows.length) {
                <p class="muted" i18n>Әзірге ешкім қосылмады. Кодты оқушыларға жіберіңіз.</p>
              } @else {
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th scope="col" i18n>Оқушы</th>
                        <th scope="col" i18n>Соңғы сабақ</th>
                        <th scope="col" i18n>Апта</th>
                        <th scope="col" i18n>Серия</th>
                        <th scope="col" i18n>Сөздер</th>
                        <th scope="col" i18n>Қадам</th>
                        <th scope="col" i18n>Дәлдік</th>
                        <th scope="col"><span class="visually-hidden" i18n>Әрекет</span></th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (r of d.rows; track r.id) {
                        <tr>
                          <th scope="row"><b>{{ r.name }}</b><small class="muted">{{ r.email }}</small></th>
                          <td [attr.data-label]="lastLabel">
                            @if (r.last_active) {
                              {{ r.last_active | date: 'd MMM' }}
                            } @else {
                              <span class="muted">–</span>
                            }
                          </td>
                          <td [attr.data-label]="weekLabel">{{ r.active_days_week }}/7</td>
                          <td [attr.data-label]="streakLabel">{{ r.streak }}</td>
                          <td [attr.data-label]="wordsLabel">{{ r.words_learning + r.words_learned }}</td>
                          <td [attr.data-label]="stepLabel" [attr.title]="r.current_step_title">
                            {{ r.current_step ?? '✓' }}<span class="muted">/16</span>
                          </td>
                          <td [attr.data-label]="accuracyLabel">{{ r.accuracy_30d !== null ? r.accuracy_30d + '%' : '–' }}</td>
                          <td class="actions">
                            <button type="button" class="icon-btn" (click)="remove(d, r.id, r.name)"
                                    [attr.aria-label]="removeLabel(r.name)" [attr.title]="removeLabel(r.name)">
                              <app-icon name="close" [size]="16" />
                            </button>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            </div>
            <button type="button" class="btn btn-ghost delete" (click)="deleteGroup(d)" i18n>Топты өшіру</button>
          } @else if (selectedId()) {
            <div class="spinner" role="status"><span class="visually-hidden" i18n>Жүктелуде</span></div>
          } @else if (groups.value().length) {
            <p class="muted pick" i18n>Сол жақтан топты таңдаңыз.</p>
          }
        </section>
      </div>
    </div>
  `,
  styles: `
    .page { display: flex; flex-direction: column; gap: 16px; }
    .head { display: flex; flex-direction: column; gap: 6px; }
    .layout { display: grid; gap: 16px; align-items: start; }
    @container main (min-width: 900px) { .layout { grid-template-columns: 280px minmax(0, 1fr); } }
    .section-title { font-size: 17px; margin: 0 0 8px; }
    .groups ul { list-style: none; margin: 0 0 12px; padding: 0; display: flex; flex-direction: column; gap: 4px; }
    .groups a { display: flex; flex-direction: column; padding: 10px 12px; border-radius: var(--r-sm); color: var(--ink);
      text-decoration: none; }
    .groups a.active { background: var(--tint); }
    .groups .empty { padding: 8px 4px; }
    .create { display: flex; flex-direction: column; gap: 8px; }
    .detail { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
    .code-card { display: flex; flex-direction: column; gap: 12px; }
    .code-card p { margin: 0; }
    .code-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .code { font-size: 28px; font-weight: 700; letter-spacing: 0.15em; padding: 6px 14px; border-radius: var(--r-sm);
      background: var(--bg); }
    .mistake { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 10px 0;
      border-bottom: 1px solid var(--line); color: var(--ink); text-decoration: none; }
    .mistake:last-child { border-bottom: 0; }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
    th, td { padding: 10px 8px; text-align: left; border-bottom: 1px solid var(--line); font-weight: 400; vertical-align: top; }
    thead th { font-size: 12px; color: var(--muted); white-space: nowrap; }
    tbody th { display: flex; flex-direction: column; min-width: 140px; }
    .actions { text-align: right; }
    .icon-btn { width: 36px; height: 36px; border-radius: 18px; border: 1px solid var(--line); background: var(--surface);
      color: var(--muted); display: inline-flex; align-items: center; justify-content: center; }
    /* phone: each learner as a card instead of a wide table */
    @container main (max-width: 640px) {
      thead { display: none; }
      table, tbody { display: block; }
      tr { display: grid; grid-template-columns: 1fr 1fr; column-gap: 12px; border: 1px solid var(--line);
        border-radius: var(--r-md); padding: 10px 12px; margin-bottom: 10px; position: relative; }
      td, tbody th { display: block; border: 0; padding: 3px 0; }
      tbody th { grid-column: 1 / -1; padding-right: 44px; margin-bottom: 4px; }
      tbody th b, tbody th small { display: block; overflow-wrap: anywhere; }
      td[data-label]::before { content: attr(data-label) ': '; color: var(--muted); }
      .actions { position: absolute; top: 8px; right: 8px; padding: 0; }
    }
    .delete { align-self: flex-start; color: var(--red); }
    .pick { padding: 24px 0; }
  `,
})
export class TeacherComponent {
  private api = inject(ApiService);
  private confirm = inject(ConfirmService);
  private toasts = inject(ToastService);
  private router = inject(Router);

  /** ?group=<id> */
  readonly group = input<string>();

  protected groups = apiResource(() => this.api.teacherGroups(), [] as TeacherGroup[]);
  protected detail = signal<TeacherGroupDetail | null>(null);
  protected detailFailed = signal(false);
  protected selectedId = signal<number | null>(null);
  protected newName = signal('');
  protected busy = signal(false);

  protected lastLabel = $localize`Соңғы сабақ`;
  protected weekLabel = $localize`Апта`;
  protected streakLabel = $localize`Серия`;
  protected wordsLabel = $localize`Сөздер`;
  protected stepLabel = $localize`Қадам`;
  protected accuracyLabel = $localize`Дәлдік`;

  constructor() {
    effect(() => {
      const id = Number(this.group()) || null;
      untracked(() => {
        this.selectedId.set(id);
        this.loadDetail();
      });
    });
    // With one group (the usual case) open it at once.
    effect(() => {
      const list = this.groups.value();
      if (!this.group() && list.length === 1) {
        untracked(() => this.router.navigate([], { queryParams: { group: list[0].id }, replaceUrl: true }));
      }
    });
  }

  protected async loadDetail() {
    const id = this.selectedId();
    this.detail.set(null);
    this.detailFailed.set(false);
    if (!id) return;
    try {
      this.detail.set(await firstValueFrom(this.api.teacherGroup(id)));
    } catch {
      this.detailFailed.set(true);
    }
  }

  protected async create(event: Event) {
    event.preventDefault();
    const name = this.newName().trim();
    if (!name || this.busy()) return;
    this.busy.set(true);
    try {
      const group = await firstValueFrom(this.api.createGroup(name));
      this.newName.set('');
      this.groups.reload();
      await this.router.navigate([], { queryParams: { group: group.id } });
    } catch (e) {
      this.toasts.error(apiErrors(e).general || Object.values(apiErrors(e).fields)[0] || '');
    } finally {
      this.busy.set(false);
    }
  }

  protected async copyInvite(group: TeacherGroupDetail) {
    const text = $localize`PoliglotAi-да «${group.name}:name:» тобына қосылыңыз: «Баптаулар» → «Мұғалім тобы» → код ${group.code}:code:`;
    try {
      await navigator.clipboard.writeText(text);
      this.toasts.success($localize`Шақыру көшірілді. Оқушыларға жіберіңіз.`);
    } catch {
      this.toasts.info(text, { sticky: true });
    }
  }

  protected async newCode(group: TeacherGroupDetail) {
    const ok = await this.confirm.ask({
      title: $localize`Жаңа код жасайсыз ба?`,
      message: $localize`Ескі код жұмыс істемей қалады. Тобыңыздағы оқушылар сол күйінде қалады.`,
      confirmText: $localize`Жаңа код`,
      cancelText: $localize`Болдырмау`,
    });
    if (!ok) return;
    const updated = await firstValueFrom(this.api.newGroupCode(group.id));
    this.detail.update((d) => (d ? { ...d, code: updated.code } : d));
  }

  protected removeLabel(name: string) {
    return $localize`${name}:name: — топтан шығару`;
  }

  protected async remove(group: TeacherGroupDetail, studentId: number, name: string) {
    const ok = await this.confirm.ask({
      title: $localize`${name}:name: — топтан шығарасыз ба?`,
      message: $localize`Оқушының өз прогресі сақталады, тек сіз оны көрмейсіз.`,
      confirmText: $localize`Шығару`,
      cancelText: $localize`Болдырмау`,
    });
    if (!ok) return;
    await firstValueFrom(this.api.removeStudent(group.id, studentId));
    this.groups.reload();
    this.loadDetail();
  }

  protected async deleteGroup(group: TeacherGroupDetail) {
    const ok = await this.confirm.ask({
      title: $localize`«${group.name}:name:» тобын өшіресіз бе?`,
      message: $localize`Оқушылардың прогресі сақталады, тек топ жойылады.`,
      confirmText: $localize`Өшіру`,
      cancelText: $localize`Болдырмау`,
    });
    if (!ok) return;
    await firstValueFrom(this.api.deleteGroup(group.id));
    this.groups.reload();
    await this.router.navigate([], { queryParams: {} });
  }
}
