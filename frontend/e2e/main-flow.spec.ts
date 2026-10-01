import { execSync } from 'node:child_process';
import { Page, expect, test } from '@playwright/test';

const password = 'englishday1';
// The backend under test runs with EMAIL_CODE_OVERRIDE (DEBUG only) or REQUIRE_EMAIL_VERIFICATION=0.
const emailCode = process.env['E2E_EMAIL_CODE'] ?? '246810';

async function register(page: Page) {
  const email = `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@mail.kz`;
  await page.goto('/register');
  await page.getByLabel('Атыңыз').fill('Айгерім');
  await page.getByLabel('Электрондық пошта').fill(email);
  await page.locator('#regPassword').fill(password);
  await page.locator('#regPassword2').fill(password);
  await page.getByText('Пайдалану шарттарымен').click();
  await page.getByRole('button', { name: 'Аккаунт ашу' }).click();
  await expect(page).toHaveURL(/\/(verify|onboarding)/);
  if (page.url().includes('/verify')) {
    await expect(page.getByText(email)).toBeVisible();
    await page.getByLabel('6 таңбалы код').fill('000000');
    await expect(page.getByRole('alert')).toContainText('Код қате');
    await page.getByLabel('6 таңбалы код').fill(emailCode); // six digits submit on their own
  }
  await expect(page).toHaveURL(/\/onboarding/);
  await page.getByRole('button', { name: /^A0/ }).click();
  await page.getByRole('button', { name: /^5/ }).click();
  await page.getByRole('button', { name: 'Бастау' }).click();
  await expect(page).toHaveURL(/\/$/);
  return email;
}

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

test('private pages redirect to login', async ({ page }) => {
  await page.goto('/words');
  await expect(page).toHaveURL(/\/login\?next=%2Fwords/);
  await expect(page.getByRole('heading', { name: 'Қош келдіңіз!' })).toBeVisible();
});

test('wrong password shows one general error', async ({ page }) => {
  await page.goto('/login');
  // A fresh address each run: the lockout after 5 failures must not leak between runs on one server.
  await page.getByLabel('Электрондық пошта').fill(`nobody-${Date.now()}@mail.kz`);
  await page.locator('#loginPassword').fill('wrongpass1');
  await page.getByRole('button', { name: 'Кіру', exact: true }).last().click();
  await expect(page.getByRole('alert')).toContainText('Пошта немесе құпиясөз қате');
});

test('learner goes through table, words, trainer and chat', async ({ page }) => {
  await register(page);
  await expect(page.getByText('Күннің мақсаты')).toBeVisible();
  await noHorizontalScroll(page);

  // Table: changing the pronoun updates all nine cells.
  await page.goto('/table?verb=buy&pronoun=she');
  await expect(page.getByRole('cell', { name: /She bought\./ })).toBeVisible();
  await page.getByRole('button', { name: /^I$/ }).click();
  await expect(page.getByRole('cell', { name: /I bought\./ })).toBeVisible();
  await expect(page.getByRole('cell', { name: /Do I buy\?/ })).toBeVisible();
  await noHorizontalScroll(page);

  // Words: start learning a new word; the stats bar follows.
  await page.goto('/words');
  await page.getByRole('button', { name: 'Үйренуді бастау' }).click();
  await expect(page.getByText(/Келесі қайталау 1 күннен кейін/)).toBeVisible();
  await expect(page.locator('.stat', { hasText: 'үйреніп жүр' }).locator('dd')).toHaveText('1');

  // Trainer: a wrong answer shows the right sentence and a link to its cell.
  await page.goto('/trainer');
  const input = page.getByLabel('Сіздің сөйлеміңіз');
  await input.fill('xyz');
  await input.press('Enter');
  await expect(page.getByText('Дұрысы:')).toBeVisible();
  await expect(page.getByRole('link', { name: /кестеде көру/ })).toBeVisible();
  await noHorizontalScroll(page);

  // Chat (offline tutor without an API key): the correction is tied to a table cell.
  await page.goto('/chat');
  await page.getByRole('button', { name: 'Бастау' }).click();
  const chatInput = page.getByLabel('Сіздің жауабыңыз');
  await chatInput.fill('I buyed a new phone.');
  await chatInput.press('Enter');
  await expect(page.locator('.correction')).toContainText('bought');
  await expect(page.locator('.correction a')).toHaveAttribute('href', /tense=past/);
  await noHorizontalScroll(page);

  // Logout closes private pages.
  await page.goto('/course');
  const logout = page.getByRole('button', { name: 'Аккаунттан шығу' }).locator('visible=true').first();
  await logout.click();
  const dialog = page.getByRole('dialog', { name: 'Аккаунттан шығасыз ба?' });
  await dialog.getByRole('button', { name: 'Қалу' }).click();
  await expect(page).toHaveURL(/\/course/);
  await logout.click();
  await dialog.getByRole('button', { name: 'Шығу' }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto('/trainer');
  await expect(page).toHaveURL(/\/login/);
});

test('the session survives a reload and an expired access token', async ({ page, context }) => {
  await register(page);
  await page.reload();
  await expect(page.getByText('Күннің мақсаты')).toBeVisible();

  // The 15-minute access token is gone: the refresh cookie brings the learner back in silently.
  const cookies = await context.cookies();
  await context.clearCookies();
  await context.addCookies(cookies.filter((c) => c.name !== 'access_token'));
  await page.goto('/words');
  await expect(page).toHaveURL(/\/words/);
});

test('login fields are recognisable by password managers', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('#loginEmail')).toHaveAttribute('autocomplete', 'username');
  await expect(page.locator('#loginEmail')).toHaveAttribute('name', 'email');
  await expect(page.locator('#loginPassword')).toHaveAttribute('autocomplete', 'current-password');
  await expect(page.locator('#loginPassword')).toHaveAttribute('name', 'password');
});

test('leaving a started training asks first', async ({ page }) => {
  await register(page);
  await page.goto('/trainer');
  await page.getByLabel('Сіздің сөйлеміңіз').fill('She will');
  const nav = page.locator('aside nav, nav.bottom-nav').locator('visible=true').first();
  await nav.getByRole('link', { name: /Басты бет/ }).click();

  const dialog = page.getByRole('dialog', { name: 'Жаттығудан шығасыз ба?' });
  await expect(dialog).toBeVisible();
  await page.keyboard.press('Escape'); // "stay" is the default
  await expect(page).toHaveURL(/\/trainer/);
  await expect(page.getByLabel('Сіздің сөйлеміңіз')).toHaveValue('She will');

  await nav.getByRole('link', { name: /Басты бет/ }).click();
  await dialog.getByRole('button', { name: 'Шығу' }).click();
  await expect(page).toHaveURL(/\/$/);
});

test('the sidebar folds into an icon rail and remembers it', async ({ page, isMobile }) => {
  test.skip(!!isMobile, 'desktop sidebar only');
  await register(page);
  const sidebar = page.locator('aside.sidebar');
  const wide = (await sidebar.boundingBox())!.width;
  await page.getByRole('button', { name: 'Мәзірді жию' }).click();
  await expect.poll(async () => (await sidebar.boundingBox())!.width).toBeLessThan(100);
  await page.reload();
  await expect.poll(async () => (await sidebar.boundingBox())!.width).toBeLessThan(100);
  await page.getByRole('button', { name: 'Мәзірді ашу' }).click();
  await expect.poll(async () => (await sidebar.boundingBox())!.width).toBe(wide);
});

test('switching the scenario in the middle of a dialog asks first', async ({ page }) => {
  await register(page);
  await page.goto('/chat');
  await page.getByRole('button', { name: 'Бастау' }).click();
  await page.getByLabel('Сіздің жауабыңыз').fill('I like tea.');
  await page.getByLabel('Сіздің жауабыңыз').press('Enter');
  await expect(page.locator('.msg.me:not(.pending)')).toHaveCount(1);

  await page.getByRole('button', { name: 'Әуежайда' }).click();
  const dialog = page.getByRole('dialog', { name: 'Жаңа диалог бастайсыз ба?' });
  await expect(dialog).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.msg.me')).toHaveCount(1);

  await page.getByRole('button', { name: 'Әуежайда' }).click();
  await dialog.getByRole('button', { name: 'Жаңасын бастау' }).click();
  await expect(page.locator('.msg.me')).toHaveCount(0);
});

test('the daily word limit can be changed in the settings', async ({ page }) => {
  await register(page);
  await page.getByRole('link', { name: 'Баптаулар' }).locator('visible=true').first().click();
  await expect(page.getByRole('heading', { name: 'Баптаулар' })).toBeVisible();
  const twenty = page.getByRole('button', { name: /^20 ~/ }); // 20 words a day (not the 20:00 reminder)
  await twenty.click();
  await page.getByRole('button', { name: 'Сақтау' }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto('/settings');
  await expect(twenty).toHaveAttribute('aria-pressed', 'true');
});

test('the stats bar fits a phone without breaking words', async ({ page, isMobile }) => {
  test.skip(!isMobile, 'phone layout');
  await register(page);
  const bar = page.locator('header.topbar');
  expect((await bar.boundingBox())!.height).toBeLessThan(110);
  for (const label of await page.locator('.stat dt').all()) {
    const box = await label.boundingBox();
    if (box && box.height > 0) expect(box.height).toBeLessThan(20); // one line
  }
  await noHorizontalScroll(page);
});

test('a course step: short lessons with practice, then the check opens the next step', async ({ page }) => {
  await register(page);
  await page.goto('/course');
  await expect(page.locator('.steps li').nth(1)).toContainText('жабық');
  await page.locator('.steps li').first().getByRole('link', { name: 'Ашу' }).click();
  await expect(page).toHaveURL(/\/course\/1$/);
  await expect(page.getByRole('heading', { name: 'Негізгі кесте' })).toBeVisible();
  await expect(page.getByText('Қалай өтеміз')).toBeVisible();

  // Lesson 1: the next button waits for the practice; a wrong pick explains the rule.
  await expect(page.getByText('Сабақ 1 / 8')).toBeVisible();
  const next = page.getByRole('button', { name: /Келесі сабақ|Тестке өту/ });
  await expect(next).toBeDisabled();
  await page.locator('.pq').first().getByRole('button', { name: 'speaks' }).click();
  await expect(page.locator('.why').first()).toContainText('Дұрысы: speak');

  const finishLesson = async () => {
    for (const q of await page.locator('.pq').all()) {
      const first = q.locator('.chip').first();
      if (await first.isEnabled()) await first.click();
    }
    await next.click();
  };
  await finishLesson();
  await expect(page.getByText('Сабақ 2 / 8')).toBeVisible();

  // The learner resumes where they stopped.
  await page.reload();
  await expect(page.getByText('Сабақ 2 / 8')).toBeVisible();
  for (let i = 2; i <= 8; i++) await finishLesson();

  await expect(page.getByRole('heading', { name: /Тест · 7 сұрақ/ })).toBeVisible();
  const choices = ['Does', 'went', 'will', 'does'];
  const typedAnswers = ["I didn't buy a car", 'She watches TV', 'Will you help me'];
  const questions = page.locator('.questions > li');
  for (const [i, option] of choices.entries()) {
    await questions.nth(i).getByRole('radio', { name: option }).click();
  }
  for (const [i, text] of typedAnswers.entries()) {
    await questions.nth(choices.length + i).getByRole('textbox').fill(i === 2 ? 'no idea' : text);
  }
  await page.getByRole('button', { name: 'Тексеру' }).click();
  await expect(page.locator('#checkResult')).toContainText('86%');
  await expect(page.locator('#checkResult')).toContainText('2-қадам ашылды');
  await noHorizontalScroll(page);

  await page.getByRole('button', { name: '2-қадамға өту' }).click();
  await expect(page.getByRole('heading', { name: 'Сұраулы сөздер' })).toBeVisible();
});

/** A stand-in for the browser's speech recognition: "hears" the given sentence, word by word. */
async function fakeMicrophone(page: Page, sentence: string, error?: string) {
  await page.addInitScript(
    ([text, failure]) => {
      class FakeRecognition {
        lang = '';
        interimResults = false;
        continuous = false;
        maxAlternatives = 1;
        onresult: ((e: unknown) => void) | null = null;
        onerror: ((e: unknown) => void) | null = null;
        onend: (() => void) | null = null;
        start() {
          setTimeout(() => {
            if (failure) {
              this.onerror?.({ error: failure });
            } else {
              const words = text!.split(' ');
              this.onresult?.({ resultIndex: 0, results: [{ isFinal: false, 0: { transcript: words[0] } }] });
              this.onresult?.({ resultIndex: 0, results: [{ isFinal: true, 0: { transcript: text } }] });
            }
            this.onend?.();
          }, 200);
        }
        stop() {}
        abort() {}
      }
      for (const name of ['SpeechRecognition', 'webkitSpeechRecognition']) {
        Object.defineProperty(window, name, { value: FakeRecognition, configurable: true, writable: true });
      }
    },
    [sentence, error] as const,
  );
}

test('the learner can say the sentence in the trainer and the chat', async ({ page }) => {
  await fakeMicrophone(page, 'I like green tea');
  await register(page);

  await page.goto('/trainer');
  await page.getByRole('button', { name: 'Айтып жауап беру' }).click();
  await expect(page.locator('app-toasts')).toContainText('Біз дыбысты сақтамаймыз'); // shown once
  await expect(page.getByLabel('Сіздің сөйлеміңіз')).toHaveValue('I like green tea');
  await page.getByRole('button', { name: 'Тексеру' }).click();
  await expect(page.locator('#answerFeedback')).toContainText(/Дұрыс|Дұрысы/);

  await page.goto('/chat');
  await page.getByRole('button', { name: 'Бастау' }).click();
  await page.getByRole('button', { name: 'Айтып жауап беру' }).click();
  await expect(page.getByLabel('Сіздің жауабыңыз')).toHaveValue('I like green tea');
  await page.getByLabel('Сіздің жауабыңыз').press('Enter');
  await expect(page.locator('.msg.me')).toContainText('I like green tea');
});

test('a blocked microphone is explained', async ({ page }) => {
  await fakeMicrophone(page, '', 'not-allowed');
  await register(page);
  await page.goto('/trainer');
  await page.getByRole('button', { name: 'Айтып жауап беру' }).click();
  await expect(page.locator('app-toasts')).toContainText('Микрофонға рұқсат жоқ');
});

test('saying a new word gives pronunciation feedback', async ({ page }) => {
  await fakeMicrophone(page, 'have');
  await register(page);
  await page.goto('/words');
  await expect(page.locator('.en')).toHaveText('have');
  await page.getByRole('button', { name: 'Сөзді айтып көру' }).click();
  await expect(page.locator('.said')).toContainText('Жақсы айттыңыз!');
});

test('the tutor reply streams in, and a failed send gives the line back', async ({ page }) => {
  await register(page);
  await page.goto('/chat');
  await page.getByRole('button', { name: 'Бастау' }).click();
  await expect(page.locator('.msg.ai')).toHaveCount(1);

  // Real stream from the offline tutor: the learner's line and the reply both land in the feed.
  await page.getByLabel('Сіздің жауабыңыз').fill('I like tea.');
  await page.getByLabel('Сіздің жауабыңыз').press('Enter');
  await expect(page.locator('.msg.me').first()).toContainText('I like tea.');
  await expect(page.locator('.msg.me:not(.pending)')).toHaveCount(1); // saved once the reply is complete
  await expect(page.locator('.bubble.streaming, .bubble.typing')).toHaveCount(0);
  await expect(page.locator('.msg.ai')).toHaveCount(2);
  await expect(page.getByLabel('Сіздің жауабыңыз')).toHaveValue('');

  // The tutor is unavailable halfway: an error event, and the text comes back to send again.
  await page.route('**/messages/stream/', (route) =>
    route.fulfill({
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
      body:
        'event: reply\ndata: {"text": "Half"}\n\n' +
        'event: error\ndata: {"detail": "AI-әңгімелесуші қазір қолжетімсіз.", "code": "unavailable", "status": 503}\n\n',
    }),
  );
  await page.getByLabel('Сіздің жауабыңыз').fill('Do you like coffee?');
  await page.getByLabel('Сіздің жауабыңыз').press('Enter');
  await expect(page.locator('.alert')).toContainText('қолжетімсіз');
  await expect(page.getByLabel('Сіздің жауабыңыз')).toHaveValue('Do you like coffee?');
  await expect(page.locator('.msg.ai')).toHaveCount(2);
});

test('reminder emails can be moved to another hour or turned off', async ({ page }) => {
  await register(page);
  await page.goto('/settings');
  await page.getByRole('button', { name: '21:00' }).click();
  await page.getByRole('button', { name: 'Сақтау' }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto('/settings');
  await expect(page.getByRole('button', { name: '21:00' })).toHaveAttribute('aria-pressed', 'true');
  await page.getByLabel('Сабақ болмаған күні поштаға еске салу').uncheck();
  await expect(page.getByRole('button', { name: '21:00' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Сақтау' }).click();
  await page.goto('/settings');
  await expect(page.getByLabel('Сабақ болмаған күні поштаға еске салу')).not.toBeChecked();
});

test('a first word earns a badge; the progress page shows the week and the badges', async ({ page }) => {
  await register(page);
  await page.goto('/words');
  await page.getByRole('button', { name: 'Үйренуді бастау' }).click();
  await expect(page.locator('app-toasts')).toContainText('🏆 Алғашқы сөз');

  // The stats bar opens the progress page.
  await page.locator('a.stats-link').click();
  await expect(page).toHaveURL(/\/progress$/);
  await expect(page.getByRole('heading', { name: 'Прогресс' })).toBeVisible();
  await expect(page.locator('app-week-chart .col')).toHaveCount(7);
  await expect(page.locator('app-week-chart .value')).toHaveText('1'); // only the busiest day is labelled
  await page.locator('app-week-chart .col').last().hover();
  await expect(page.getByRole('tooltip')).toContainText('Жаңа сөздер');
  await page.getByText('Кесте түрінде').click();
  await expect(page.locator('app-week-chart tbody tr')).toHaveCount(7);
  await expect(page.locator('.badges li.earned')).toContainText('Алғашқы сөз');
  await expect(page.locator('.badges li:not(.earned)').first().locator('.meter')).toBeVisible();
  await noHorizontalScroll(page);
});

test('the placement test credits known steps and sets the level', async ({ page }) => {
  await page.goto('/register');
  await page.getByLabel('Атыңыз').fill('Айгерім');
  await page.getByLabel('Электрондық пошта').fill(`pl-${Date.now()}-${Math.floor(Math.random() * 1e6)}@mail.kz`);
  await page.locator('#regPassword').fill(password);
  await page.locator('#regPassword2').fill(password);
  await page.getByText('Пайдалану шарттарымен').click();
  await page.getByRole('button', { name: 'Аккаунт ашу' }).click();
  await expect(page).toHaveURL(/\/(verify|onboarding)/);
  if (page.url().includes('/verify')) await page.getByLabel('6 таңбалы код').fill(emailCode);
  await expect(page).toHaveURL(/\/onboarding/);

  await page.getByRole('link', { name: /тестпен анықтайық/ }).click();
  await expect(page.getByRole('heading', { name: 'Деңгейді анықтайық' })).toBeVisible();
  await page.getByRole('button', { name: 'Бастау' }).click();
  // Steps 1-3 known, then "I don't know" three times in a row ends the test.
  for (const answer of ['drink', 'Does', 'went', "won't", 'Where', 'How many', 'are', 'was']) {
    await page.getByRole('button', { name: answer, exact: true }).click();
  }
  for (let i = 0; i < 3; i++) await page.getByRole('button', { name: 'Білмеймін' }).click();

  await expect(page.getByRole('heading', { name: 'Сіздің деңгейіңіз: A1' })).toBeVisible();
  await expect(page.locator('.alert-ok')).toContainText('1–3-қадамдары есептелді');
  await page.getByRole('button', { name: 'Жалғастыру' }).click();
  await expect(page).toHaveURL(/\/onboarding/);
  await expect(page.getByRole('button', { name: /^A1/ })).toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', { name: /^10/ }).click();
  await page.getByRole('button', { name: 'Бастау' }).click();
  await expect(page).toHaveURL(/\/$/);

  await page.goto('/course');
  const steps = page.locator('.steps li');
  await expect(steps.nth(2).getByRole('link', { name: 'Қайталау' })).toBeVisible(); // step 3 done
  await expect(steps.nth(3).getByRole('link', { name: 'Ашу' })).toBeVisible(); // step 4 open
});

/** Runs a Django management command (E2E_MANAGE is e.g. "docker compose exec -T backend python manage.py"). */
function manage(args: string) {
  execSync(`${process.env['E2E_MANAGE']} ${args}`, { stdio: 'pipe', shell: '/bin/sh' });
}

test('a teacher creates a group, a learner joins with the code, the teacher sees them', async ({ browser }) => {
  test.skip(!process.env['E2E_MANAGE'], 'needs E2E_MANAGE to give the teacher role');
  const teacherPage = await (await browser.newContext({ serviceWorkers: 'block' })).newPage();
  const teacherEmail = await register(teacherPage);
  manage(`grant_teacher ${teacherEmail}`);
  await teacherPage.goto('/settings');
  await teacherPage.getByRole('link', { name: 'Мұғалім кабинетін ашу' }).click();
  await teacherPage.getByPlaceholder('Мысалы: 7А сынып').fill('7А сынып');
  await teacherPage.getByRole('button', { name: 'Топ құру' }).click();
  const code = (await teacherPage.locator('.code').textContent())!.trim();
  expect(code).toMatch(/^[A-Z2-9]{6}$/);

  const learnerPage = await (await browser.newContext({ serviceWorkers: 'block' })).newPage();
  await register(learnerPage);
  await learnerPage.goto('/settings');
  await expect(learnerPage.getByText('AI-чаттағы хабарламаларыңызды көрмейді')).toBeVisible();
  await learnerPage.getByPlaceholder('Мұғалім берген код').fill(code.toLowerCase());
  await learnerPage.getByRole('button', { name: 'Қосылу' }).click();
  await expect(learnerPage.locator('.group-row')).toContainText('7А сынып');

  await teacherPage.reload();
  await expect(teacherPage.locator('tbody tr')).toHaveCount(1);
  await expect(teacherPage.locator('tbody tr')).toContainText('Айгерім');
});
