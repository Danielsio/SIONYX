import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test('loads the landing page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/SIONYX/i);
  });

  test('shows the app name/branding', async ({ page }) => {
    await page.goto('/');
    const heading = page.locator('text=SIONYX');
    await expect(heading.first()).toBeVisible();
  });

  test('has a login link or button', async ({ page }) => {
    await page.goto('/');
    const loginLink = page.locator('a[href*="login"], button:has-text("כניסה"), a:has-text("כניסה"), button:has-text("Login"), a:has-text("Login")');
    await expect(loginLink.first()).toBeVisible();
  });

  test('has a registration section', async ({ page }) => {
    await page.goto('/');
    const regSection = page.locator('text=/הרשמ|register/i');
    await expect(regSection.first()).toBeVisible();
  });

  test('navigates to login page', async ({ page }) => {
    await page.goto('/');
    const loginLink = page.locator('a[href*="login"]');
    if (await loginLink.count() > 0) {
      await loginLink.first().click();
      await expect(page).toHaveURL(/login/);
    }
  });
});
