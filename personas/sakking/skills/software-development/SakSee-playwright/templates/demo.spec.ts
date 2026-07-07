import { test, expect } from '@playwright/test';

// Baseline patterns: title/text assertions, API validation, click + state-change.

test('title and text assertions', async ({ page }) => {
  await page.goto('https://example.com', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveTitle(/Example Domain/);
  await expect(page.locator('h1')).toHaveText('Example Domain');
});

test('API endpoint validation', async ({ request }) => {
  const res = await request.get('https://example.com');
  expect(res.ok()).toBeTruthy();
  expect(res.status()).toBe(200);
});

test('click and state-change', async ({ page }) => {
  await page.goto('https://example.com', { waitUntil: 'domcontentloaded' });
  // example.com has a "More information..." link to iana.org
  await page.click('a');
  await expect(page).toHaveURL(/iana\.org/);
});
