import { Page, expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';

const emailCode = process.env['E2E_EMAIL_CODE'] ?? '246810';

async function signUp(page: Page) {
  const email = `acc-${Date.now()}-${Math.floor(Math.random() * 1e6)}@mail.kz`;
  await page.goto('/register');
  await page.getByLabel('Атыңыз').fill('Айгерім');
  await page.getByLabel('Электрондық пошта').fill(email);
  await page.locator('#regPassword').fill('englishday1');
  await page.locator('#regPassword2').fill('englishday1');
  await page.getByText('Пайдалану шарттарымен').click();
  await page.getByRole('button', { name: 'Аккаунт ашу' }).click();
  await expect(page).toHaveURL(/\/(verify|onboarding)/);
  if (page.url().includes('/verify')) await page.getByLabel('6 таңбалы код').fill(emailCode);
  await page.getByRole('button', { name: 'Бастау' }).click();
  await expect(page).toHaveURL(/\/$/);
  return email;
}

async function logIn(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.locator('#loginEmail').fill(email);
  await page.locator('#loginPassword').fill(password);
  await page.getByRole('button', { name: 'Кіру', exact: true }).last().click();
}

test('change the password, download the data, delete the account', async ({ page, context }) => {
  const email = await signUp(page);
  await page.goto('/settings');
  const account = page.locator('app-account-section');
  await expect(account).toContainText(email);

  // Password: a wrong current one is shown at its field, the right one saves.
  await account.getByRole('button', { name: 'Құпиясөзді өзгерту' }).click();
  await account.locator('#oldPassword').fill('notmypass1');
  await account.locator('#changePassword').fill('springday2');
  await account.locator('#changePassword2').fill('springday2');
  await account.getByRole('button', { name: 'Құпиясөзді сақтау' }).click();
  await expect(account.locator('#oldPasswordError')).toHaveText('Ағымдағы құпиясөз қате.');
  await account.locator('#oldPassword').fill('englishday1');
  await account.getByRole('button', { name: 'Құпиясөзді сақтау' }).click();
  await expect(page.locator('app-toasts')).toContainText('Құпиясөз өзгертілді');
  await expect(account.locator('#oldPassword')).toHaveCount(0);

  // Data: one JSON file with the account in it.
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    account.getByRole('button', { name: 'Деректерімді жүктеу' }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^poliglotai-\d{4}-\d{2}-\d{2}\.json$/);
  const data = JSON.parse(readFileSync((await download.path())!, 'utf8'));
  expect(data.account.email).toBe(email);
  expect(Array.isArray(data.words)).toBeTruthy();

  // The new password works on another device (a fresh login).
  await context.clearCookies();
  await logIn(page, email, 'springday2');
  await expect(page).toHaveURL(/\/$/);

  // Delete: the password, then a confirmation; afterwards the login is gone.
  await page.goto('/settings');
  await account.getByRole('button', { name: 'Аккаунтты жою' }).click();
  await account.locator('#deletePassword').fill('springday2');
  await account.getByRole('button', { name: 'Біржола жою' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Иә, жою' }).click();
  await expect(page).toHaveURL(/\/register/);
  await expect(page.locator('app-toasts')).toContainText('Аккаунт жойылды');
  await logIn(page, email, 'springday2');
  await expect(page.getByRole('alert').first()).toContainText('қате');
});

test('the delete confirmation can be cancelled', async ({ page }) => {
  await signUp(page);
  await page.goto('/settings');
  const account = page.locator('app-account-section');
  await account.getByRole('button', { name: 'Аккаунтты жою' }).click();
  await account.locator('#deletePassword').fill('englishday1');
  await account.getByRole('button', { name: 'Біржола жою' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Бас тарту' }).click();
  await account.getByRole('button', { name: 'Бас тарту' }).click();
  await expect(account.locator('#deletePassword')).toHaveCount(0);
  await page.reload();
  await expect(page.locator('app-account-section')).toBeVisible();
});

test('a teacher signs up like a learner and opens the cabinet with the school code', async ({ page }) => {
  const code = process.env['E2E_TEACHER_CODE'];
  test.skip(!code, 'needs E2E_TEACHER_CODE (TEACHER_INVITE_CODE on the server)');
  await signUp(page);
  await page.goto('/settings');
  // A wrong group code says so (not "connection error").
  await page.getByLabel('Мұғалім берген код').fill('ZZZZZZ');
  await page.getByRole('button', { name: 'Қосылу' }).click();
  await expect(page.locator('app-onboarding [role="alert"]').first()).toContainText('Мұндай код жоқ');
  await page.getByText('Мен мұғаліммін').click();
  await page.getByLabel('Мұғалім коды').fill('WRONG-CODE');
  await page.getByRole('button', { name: 'Растау' }).click();
  await expect(page.locator('.teacher-code [role="alert"]')).toContainText('Код қате');
  await page.getByLabel('Мұғалім коды').fill(code!);
  await page.getByRole('button', { name: 'Растау' }).click();
  await expect(page.locator('app-toasts')).toContainText('Мұғалім кабинеті ашылды');
  await page.getByRole('link', { name: 'Мұғалім кабинетін ашу' }).click();
  await expect(page).toHaveURL(/\/teacher/);
});
