import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('landing page renders on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const heading = page.locator('text=SIONYX');
    await expect(heading.first()).toBeVisible();
  });

  test('login page renders on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/admin/login');
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput.first()).toBeVisible();
  });

  test('landing page renders on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    const heading = page.locator('text=SIONYX');
    await expect(heading.first()).toBeVisible();
  });

  test('landing page renders on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    const heading = page.locator('text=SIONYX');
    await expect(heading.first()).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('unknown routes redirect to landing', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await page.waitForTimeout(1000);
    // Should redirect to landing
    await expect(page).toHaveURL('/');
  });
});
