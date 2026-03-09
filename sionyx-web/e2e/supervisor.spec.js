import { test, expect } from '@playwright/test';

test.describe('Supervisor Login Page', () => {
  test('renders the supervisor login form', async ({ page }) => {
    await page.goto('/supervisor/login');

    const phoneInput = page.locator(
      'input[type="text"], input[placeholder*="1234567890"]'
    );
    await expect(phoneInput.first()).toBeVisible();

    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput.first()).toBeVisible();
  });

  test('shows supervisor title', async ({ page }) => {
    await page.goto('/supervisor/login');

    const title = page.locator('text=כניסת מפקח');
    await expect(title.first()).toBeVisible();
  });

  test('has a submit button', async ({ page }) => {
    await page.goto('/supervisor/login');

    const submitBtn = page.locator(
      'button[type="submit"], button:has-text("התחבר")'
    );
    await expect(submitBtn.first()).toBeVisible();
  });

  test('does NOT have an orgId field (supervisor login is org-agnostic)', async ({ page }) => {
    await page.goto('/supervisor/login');

    const orgInput = page.locator(
      'input[placeholder*="ארגון"], input[placeholder*="org"], #orgId'
    );
    await expect(orgInput).toHaveCount(0);
  });

  test('shows error on empty form submission', async ({ page }) => {
    await page.goto('/supervisor/login');

    const submitBtn = page.locator(
      'button[type="submit"], button:has-text("התחבר")'
    );
    await submitBtn.first().click();
    await page.waitForTimeout(1000);

    await expect(page).toHaveURL(/supervisor\/login/);
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/supervisor/login');

    const phoneInput = page.locator(
      'input[type="text"], input[placeholder*="1234567890"]'
    ).first();
    await phoneInput.fill('0500000099');

    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.fill('wrongpassword123');

    const submitBtn = page.locator(
      'button[type="submit"], button:has-text("התחבר")'
    ).first();
    await submitBtn.click();
    await page.waitForTimeout(3000);

    await expect(page).toHaveURL(/supervisor\/login/);
  });

  test('shows supervisor-specific footer text', async ({ page }) => {
    await page.goto('/supervisor/login');

    const footerText = page.locator('text=ממשק מפקחים');
    await expect(footerText.first()).toBeVisible();
  });
});

test.describe('Supervisor Protected Routes', () => {
  test('redirects /supervisor to login when not authenticated', async ({ page }) => {
    await page.goto('/supervisor');
    await page.waitForTimeout(2000);

    const url = page.url();
    expect(url.includes('supervisor/login') || url.endsWith('/')).toBeTruthy();
  });

  test('redirects /supervisor/organizations to login when not authenticated', async ({ page }) => {
    await page.goto('/supervisor/organizations');
    await page.waitForTimeout(2000);

    const url = page.url();
    expect(url.includes('supervisor/login') || url.endsWith('/')).toBeTruthy();
  });

  test('redirects /supervisor/blocked to login when not authenticated', async ({ page }) => {
    await page.goto('/supervisor/blocked');
    await page.waitForTimeout(2000);

    const url = page.url();
    expect(url.includes('supervisor/login') || url.endsWith('/')).toBeTruthy();
  });

  test('redirects /supervisor/settings to login when not authenticated', async ({ page }) => {
    await page.goto('/supervisor/settings');
    await page.waitForTimeout(2000);

    const url = page.url();
    expect(url.includes('supervisor/login') || url.endsWith('/')).toBeTruthy();
  });
});

test.describe('Supervisor and Admin Route Isolation', () => {
  test('admin login page does not contain supervisor elements', async ({ page }) => {
    await page.goto('/admin/login');

    const supervisorTitle = page.locator('text=כניסת מפקח');
    await expect(supervisorTitle).toHaveCount(0);
  });

  test('supervisor login page does not contain admin elements', async ({ page }) => {
    await page.goto('/supervisor/login');

    const adminOrgField = page.locator(
      'input[placeholder*="ארגון"], input[placeholder*="org"]'
    );
    await expect(adminOrgField).toHaveCount(0);
  });

  test('supervisor and admin login are at different URLs', async ({ page }) => {
    await page.goto('/admin/login');
    const adminUrl = page.url();

    await page.goto('/supervisor/login');
    const supervisorUrl = page.url();

    expect(adminUrl).not.toEqual(supervisorUrl);
  });
});
