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
  await page.getByLabel('Электрондық пошта').fill('nobody@mail.kz');
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
  await expect(page.locator('.msg.me')).toHaveCount(1);

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
  await page.getByRole('button', { name: /^20/ }).click();
  await page.getByRole('button', { name: 'Сақтау' }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto('/settings');
  await expect(page.getByRole('button', { name: /^20/ })).toHaveAttribute('aria-pressed', 'true');
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
