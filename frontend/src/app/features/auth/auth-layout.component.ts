import { ChangeDetectionStrategy, Component } from '@angular/core';
import { LogoComponent } from '../../shared/logo.component';

const PREVIEW = [
  'Will she buy?', 'She will buy.', "She won't buy.",
  'Does she buy?', 'She buys.', "She doesn't buy.",
  'Did she buy?', 'She bought.', "She didn't buy.",
];

/** Two columns on desktop (red pitch panel + form), a single column on the phone. */
@Component({
  selector: 'app-auth-layout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LogoComponent],
  template: `
    <div class="wrap">
      <aside class="pitch" aria-hidden="true">
        <app-logo [inverse]="true" />
        <h1 i18n>Ағылшынша бірінші күннен сөйлеңіз</h1>
        <p i18n>Етістік кестесі, сөз карточкалары және AI-әңгімелесуші — бір жерде, қазақ тілінде.</p>
        <div class="mini">
          @for (s of preview; track $index) {
            <span [class.hot]="$index === 4">{{ s }}</span>
          }
        </div>
        <div class="facts">
          <span><b>9</b><ng-container i18n>етістік формасы</ng-container></span>
          <span><b>6</b><ng-container i18n>қайталау кезеңі</ng-container></span>
          <span><b>AI</b><ng-container i18n>әңгімелесуші</ng-container></span>
        </div>
      </aside>
      <main class="side">
        <div class="mobile-logo"><app-logo /></div>
        <div class="box"><ng-content /></div>
      </main>
    </div>
  `,
  styles: `
    .wrap { display: flex; min-height: 100vh; background: var(--surface); }
    .pitch { display: none; width: 44%; max-width: 640px; flex-shrink: 0; background: #d7262e; color: #fff;
      padding: 48px 64px; flex-direction: column; }
    .pitch h1 { margin-top: 88px; font-size: 44px; line-height: 1.15; }
    .pitch p { margin: 20px 0 0; font-size: 18px; max-width: 460px; }
    .mini { margin-top: 40px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; font-size: 15px; }
    .mini span { border-radius: 12px; padding: 14px 12px; background: rgba(255,255,255,.14); }
    .mini span.hot { background: #fff; color: #a8151c; font-weight: 600; }
    .facts { margin-top: auto; display: flex; gap: 32px; font-size: 15px; padding-top: 32px; }
    .facts b { font-family: var(--font-display); font-size: 22px; display: block; }
    .side { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 24px 16px 40px; }
    .mobile-logo { align-self: flex-start; margin-bottom: 32px; }
    .box { width: 100%; max-width: 440px; display: flex; flex-direction: column; gap: 24px; }
    @media (min-width: 1024px) {
      .pitch { display: flex; }
      .side { justify-content: center; padding: 48px; }
      .mobile-logo { display: none; }
    }
  `,
})
export class AuthLayoutComponent {
  protected preview = PREVIEW;
}
