import { Page, expect, test } from '@playwright/test';

const password = 'englishday1';

async function register(page: Page) {
  const email = `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@mail.kz`;
  await page.goto('/register');
  await page.getByLabel('Атыңыз').fill('Айгерім');
  await page.getByLabel('Электрондық пошта').fill(email);
  await page.locator('#regPassword').fill(password);
  await page.locator('#regPassword2').fill(password);
  await page.getByText('Пайдалану шарттарымен').click();
  await page.getByRole('button', { name: 'Аккаунт ашу' }).click();
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
  const logout = page.getByRole('button', { name: 'Шығу' }).locator('visible=true').first();
  await logout.click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto('/trainer');
  await expect(page).toHaveURL(/\/login/);
});
