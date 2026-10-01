import { Page, expect, test } from '@playwright/test';

const emailCode = process.env['E2E_EMAIL_CODE'] ?? '246810';

async function signUp(page: Page) {
  await page.goto('/register');
  await page.getByLabel('Атыңыз').fill('Айгерім');
  await page.getByLabel('Электрондық пошта').fill(`err-${Date.now()}-${Math.floor(Math.random() * 1e6)}@mail.kz`);
  await page.locator('#regPassword').fill('englishday1');
  await page.locator('#regPassword2').fill('englishday1');
  await page.getByText('Пайдалану шарттарымен').click();
  await page.getByRole('button', { name: 'Аккаунт ашу' }).click();
  await expect(page).toHaveURL(/\/(verify|onboarding)/);
  if (page.url().includes('/verify')) await page.getByLabel('6 таңбалы код').fill(emailCode);
  await page.getByRole('button', { name: 'Бастау' }).click();
  await expect(page).toHaveURL(/\/$/);
}

const toasts = (page: Page) => page.locator('app-toasts');

test('a lost connection is announced once, and its return too', async ({ page, context }) => {
  await signUp(page);
  await context.setOffline(true);
  await expect(toasts(page).getByText('Интернет жоқ')).toHaveCount(1);
  await context.setOffline(false);
  await expect(toasts(page).getByText('Байланыс қалпына келді')).toBeVisible();
  await expect(toasts(page).getByText('Интернет жоқ')).toHaveCount(0);
});

test('a server error shows a pop-up and the block offers a retry', async ({ page }) => {
  await signUp(page);
  let fail = true;
  await page.route('**/api/course/', (route) =>
    fail
      ? route.fulfill({ status: 500, json: { detail: 'Серверде қате болды. Бірнеше минуттан кейін қайталап көріңіз.', code: 'server_error' } })
      : route.fallback(),
  );
  await page.goto('/course');
  await expect(toasts(page).getByRole('alert')).toContainText('Серверде қате болды');
  const block = page.locator('app-load-error');
  await expect(block).toContainText('Жүктеу мүмкін болмады');

  fail = false;
  await block.getByRole('button', { name: 'Қайталау' }).click();
  await expect(page.getByText('Негізгі кесте').first()).toBeVisible();
  await expect(block).toHaveCount(0);
});

test('the home screen survives failing requests instead of breaking', async ({ page }) => {
  await signUp(page);
  await page.route('**/api/verbs/', (route) => route.abort('failed'));
  await page.route('**/api/course/', (route) => route.abort('failed'));
  await page.goto('/');
  await expect(page.getByText('Күннің мақсаты')).toBeVisible();
  await expect(page.locator('app-load-error')).toHaveCount(2);
  // many failing requests, one pop-up
  await expect(toasts(page).getByText('Серверге қосылу мүмкін болмады')).toHaveCount(1);
});

test('a slow server says it is waking up', async ({ page }) => {
  await signUp(page);
  await page.route('**/api/trainer/task/', async (route) => {
    await new Promise((r) => setTimeout(r, 6500));
    await route.fallback();
  });
  await page.goto('/trainer');
  await expect(toasts(page).getByText('Сервер оянып жатыр')).toBeVisible({ timeout: 8000 });
  await expect(page.getByLabel('Сіздің сөйлеміңіз')).toBeVisible({ timeout: 10000 });
  await expect(toasts(page).getByText('Сервер оянып жатыр')).toHaveCount(0);
});

test('adding a word from the chat confirms with a pop-up', async ({ page }) => {
  await signUp(page);
  await page.goto('/chat');
  await page.getByRole('button', { name: 'Бастау' }).click();
  await page.getByRole('button', { name: /yesterday — кеше/ }).click();
  await expect(toasts(page).getByRole('status')).toContainText('«yesterday» карточкаларға қосылды');
});

test('cards that failed to load offer a retry instead of "all done"', async ({ page }) => {
  await signUp(page);
  let fail = true;
  await page.route('**/api/srs/today/', (route) =>
    fail ? route.fulfill({ status: 500, json: { detail: 'boom', code: 'server_error' } }) : route.fallback(),
  );
  await page.goto('/words');
  const block = page.locator('app-load-error');
  await expect(block).toContainText('Жүктеу мүмкін болмады');
  await expect(page.getByText('Бүгінге бәрі!')).toHaveCount(0);
  fail = false;
  await block.getByRole('button', { name: 'Қайталау' }).click();
  await expect(page.getByRole('button', { name: 'Үйренуді бастау' })).toBeVisible();
});

test('reviews check the word: pick the translation, pick what you hear, type it', async ({ page }) => {
  await signUp(page);
  const card = (id: number, word: string, kk: string, stage: number, quiz: object) => ({
    id, word, translation_kk: kk, ipa: '', is_verb: false, past: '', is_irregular: false, example_en: '',
    example_kk: '', topic: '', course_step: 1, source: 'course', status: 'learning', stage, quiz,
  });
  await page.route('**/api/srs/today/', (route) =>
    route.fulfill({
      json: {
        review: [
          card(1, 'buy', 'сатып алу', 1, { mode: 'choice', options: ['ішу', 'сатып алу', 'бару', 'көру'] }),
          card(2, 'speak', 'сөйлеу', 3, { mode: 'listen', options: ['speak', 'sleep', 'spend', 'stand'] }),
          card(3, 'study', 'оқу', 5, { mode: 'type' }),
        ],
        new: [], new_limit: 10, new_left: 0, intervals: [1, 2, 4, 7, 14, 30],
      },
    }),
  );
  const verdicts: Record<string, object> = {
    1: { correct: true, almost: false, right: 'сатып алу', stage: 2 },
    2: { correct: false, almost: false, right: 'speak', stage: 2 },
    3: { correct: true, almost: true, right: 'study', stage: 6 },
  };
  await page.route('**/api/srs/*/check/', (route) => {
    const id = route.request().url().match(/srs\/(\d+)\/check/)![1];
    route.fulfill({ json: { word_id: Number(id), status: 'learning', next_review_date: null, again_today: false, ...verdicts[id] } });
  });

  await page.goto('/words');
  // 1. choice: the English word, four translations
  await expect(page.getByText('Аудармасын таңдаңыз')).toBeVisible();
  await page.getByRole('button', { name: 'сатып алу' }).click();
  await expect(page.locator('.verdict')).toContainText('Дұрыс!');

  // 2. listening: no written word, a wrong pick shows the right one and waits for "next"
  await expect(page.getByText('Тыңдап, сөзді таңдаңыз')).toBeVisible();
  await expect(page.locator('.en')).toHaveCount(0);
  await page.getByRole('button', { name: 'sleep' }).click();
  await expect(page.locator('.verdict')).toContainText('Қате. Дұрысы: speak');
  await page.getByRole('button', { name: 'Келесі' }).click();

  // 3. typing: the Kazakh word, one typo is accepted with the right spelling shown
  await expect(page.getByText('Ағылшынша жазыңыз')).toBeVisible();
  await page.getByLabel('Ағылшынша сөз').fill('studdy');
  await page.getByLabel('Ағылшынша сөз').press('Enter');
  await expect(page.locator('.verdict')).toContainText('Жазылуы: study');
  await page.getByRole('button', { name: 'Келесі' }).click();

  // The forgotten word comes back at the end of the session.
  await expect(page.getByText('Тыңдап, сөзді таңдаңыз')).toBeVisible();
});

test('a page error reaches monitoring without personal data', async ({ page }) => {
  await signUp(page);
  // Monitoring is on when the server gives a DSN; the reports go to Sentry's ingest address, caught here.
  await page.route('**/api/config/', (route) =>
    route.fulfill({ json: { sentry_dsn: 'https://public@o1.ingest.sentry.io/1', environment: 'e2e', release: 'test' } }),
  );
  const envelopes: string[] = [];
  await page.route('https://o1.ingest.sentry.io/**', (route) => {
    envelopes.push(route.request().postData() ?? '');
    return route.fulfill({ status: 200, json: {} });
  });
  await page.goto('/course?token=secret-token');
  await expect(page.getByText('Негізгі кесте').first()).toBeVisible();

  await page.evaluate(() => setTimeout(() => { throw new Error('e2e page bug'); }));
  await expect(toasts(page).getByRole('alert')).toContainText('Бірдеңе дұрыс болмады');
  await expect.poll(() => envelopes.filter((e) => e.includes('e2e page bug')).length).toBe(1);

  const event = JSON.parse(envelopes.find((e) => e.includes('e2e page bug'))!.split('\n')[2]);
  expect(event.environment).toBe('e2e');
  expect(event.user?.id).toMatch(/^\d+$/);
  expect(event.user?.email).toBeUndefined();
  expect(JSON.stringify(event)).not.toContain('secret-token');
  expect(JSON.stringify(event)).not.toContain('@mail.kz');
});
