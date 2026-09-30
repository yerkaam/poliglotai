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
