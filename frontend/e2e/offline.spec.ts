import { expect, test } from '@playwright/test';

test.use({ serviceWorkers: 'allow' });

test('the app is installable and cards work without internet', async ({ page, context }) => {
  // Sign up and onboard.
  await page.goto('/register');
  await page.getByLabel('Атыңыз').fill('Айгерім');
  await page.getByLabel('Электрондық пошта').fill(`off-${Date.now()}-${Math.floor(Math.random() * 1e6)}@mail.kz`);
  await page.locator('#regPassword').fill('englishday1');
  await page.locator('#regPassword2').fill('englishday1');
  await page.getByText('Пайдалану шарттарымен').click();
  await page.getByRole('button', { name: 'Аккаунт ашу' }).click();
  await expect(page).toHaveURL(/\/(verify|onboarding)/);
  if (page.url().includes('/verify')) await page.getByLabel('6 таңбалы код').fill(process.env['E2E_EMAIL_CODE'] ?? '246810');
  await page.getByRole('button', { name: 'Бастау' }).click();
  await expect(page).toHaveURL(/\/$/);

  // Installable: a manifest with icons, and a service worker that takes control.
  const manifest = await (await page.request.get('/manifest.webmanifest')).json();
  expect(manifest.display).toBe('standalone');
  expect(manifest.icons.some((i: { sizes: string }) => i.sizes === '512x512')).toBeTruthy();
  await page.goto('/words');
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload(); // now the page and its data requests go through the worker, which caches them
  await expect(page.getByRole('button', { name: 'Үйренуді бастау' })).toBeVisible();
  const first = await page.locator('.en').textContent();
  await page.waitForTimeout(1000);

  // Offline: the app opens from the cache, and an answer is kept on the phone. (setOffline alone does not
  // reach the service worker's own requests in Chromium, so every request leaving the browser is cut too.)
  await context.route('**/*', (route) => route.abort('internetdisconnected'));
  await context.setOffline(true);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Үйренуді бастау' })).toBeVisible();
  await page.getByRole('button', { name: 'Үйренуді бастау' }).click();
  await expect(page.locator('.note')).toContainText('Интернет жоқ');
  await page.reload();
  await expect(page.locator('.en')).not.toHaveText(first!); // the answered word is not asked again

  // Back online: the answer is sent.
  await context.unroute('**/*');
  await context.setOffline(false);
  // Sent on the "online" event, or by the retry a few seconds later if the network was not quite back yet.
  await expect(page.locator('app-toasts')).toContainText('жауап сақталды', { timeout: 15_000 });
});
