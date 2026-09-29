import { ChangeDetectionStrategy, Component, ElementRef, computed, inject, signal, viewChild } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { INTERVAL_LABELS } from '../../core/labels';
import { CourseStep } from '../../core/models';
import { ProgressStore } from '../../core/progress.store';
import { IconComponent } from '../../shared/icon.component';
import { apiErrors } from '../auth/errors';

@Component({
  selector: 'app-course',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent, RouterLink],
  templateUrl: './course.component.html',
  styleUrl: './course.component.scss',
})
export class CourseComponent {
  private api = inject(ApiService);
  protected store = inject(ProgressStore);
  private dialog = viewChild<ElementRef<HTMLDialogElement>>('resetDialog');

  protected steps = toSignal(this.api.course(), { initialValue: [] as CourseStep[] });
  protected intervals = INTERVAL_LABELS;
  protected resetting = signal(false);
  protected message = signal('');
  protected stageMax = computed(() => Math.max(1, ...(this.store.progress()?.stages.map((s) => s.count) ?? [1])));

  protected openReset() {
    this.message.set('');
    this.dialog()?.nativeElement.showModal();
  }

  protected closeReset() {
    this.dialog()?.nativeElement.close();
  }

  /** 3.5: progress is reset only after an explicit confirmation. */
  protected async confirmReset() {
    this.resetting.set(true);
    try {
      await firstValueFrom(this.api.resetProgress());
      this.store.refresh();
      this.message.set($localize`Прогресс тазартылды. Жаңадан бастауға болады.`);
      this.closeReset();
    } catch (e) {
      this.message.set(apiErrors(e).general);
    } finally {
      this.resetting.set(false);
    }
  }
}
