import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { catchError, filter, of, switchMap, tap } from 'rxjs';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { PRONOUN_KK, PRONOUNS, STATUS_KK, TENSE_KK, TENSE_RULE_KK, TENSES } from '../../core/labels';
import { Form, Pronoun, Tense, VerbForms, Word } from '../../core/models';
import { IconComponent } from '../../shared/icon.component';
import { VerbGridComponent } from '../../shared/verb-grid.component';

@Component({
  selector: 'app-table',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [VerbGridComponent, IconComponent, RouterLink],
  templateUrl: './table.component.html',
  styleUrl: './table.component.scss',
})
export class TableComponent {
  private api = inject(ApiService);
  private router = inject(Router);

  // Query parameters (?verb=buy&pronoun=she&tense=past&form=affirmative) drive the screen.
  readonly verb = input<string>();
  readonly pronoun = input<string>();
  readonly tense = input<string>();
  readonly form = input<string>();

  protected pronouns = PRONOUNS;
  protected pronounKk = PRONOUN_KK;
  protected tenses = TENSES;
  protected tenseKk = TENSE_KK;
  protected rules = TENSE_RULE_KK;
  protected statusKk = STATUS_KK;

  protected verbs = toSignal(this.api.verbs(), { initialValue: [] as Word[] });
  protected pickerOpen = signal(false);
  protected query = signal('');
  protected loadError = signal(false);

  protected currentPronoun = computed<Pronoun>(() => {
    const p = this.pronoun() as Pronoun;
    return PRONOUNS.includes(p) ? p : 'she';
  });
  protected currentVerb = computed<Word | null>(() => {
    const list = this.verbs();
    if (!list.length) return null;
    const wanted = (this.verb() ?? '').toLowerCase();
    return list.find((v) => v.word === wanted) ?? list.find((v) => v.status === 'learning') ?? list[0];
  });
  protected focusTense = computed(() => (TENSES.includes(this.tense() as Tense) ? (this.tense() as Tense) : null));
  protected focusForm = computed(() => (this.form() as Form) ?? null);

  protected filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    return this.verbs().filter((v) => v.is_verb && (!q || v.word.includes(q) || v.translation_kk.toLowerCase().includes(q)));
  });

  private request = computed(() => {
    const verb = this.currentVerb();
    return verb ? { id: verb.id, pronoun: this.currentPronoun() } : null;
  });

  // TBL: changing the pronoun or verb reloads all nine cells at once; stale answers are dropped.
  protected data = toSignal(
    toObservable(this.request).pipe(
      filter((r) => r !== null),
      tap(() => this.loadError.set(false)),
      switchMap((r) =>
        this.api.forms(r.id, r.pronoun).pipe(
          catchError(() => {
            this.loadError.set(true);
            return of(null);
          }),
        ),
      ),
    ),
    { initialValue: null as VerbForms | null },
  );

  protected setPronoun(p: Pronoun) {
    this.navigate({ pronoun: p, tense: null, form: null });
  }

  protected pick(word: Word) {
    this.pickerOpen.set(false);
    this.query.set('');
    this.navigate({ verb: word.word, tense: null, form: null });
  }

  protected onPickerKey(event: KeyboardEvent) {
    if (event.key === 'Escape') this.pickerOpen.set(false);
  }

  private navigate(params: Record<string, string | null>) {
    this.router.navigate([], { queryParams: params, queryParamsHandling: 'merge', replaceUrl: true });
  }
}
