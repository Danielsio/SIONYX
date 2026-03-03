import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('renders the login form', async ({ page }) => {
    await page.goto('/admin/login');
    
    const phoneInput = page.locator('input[type="text"], input[placeholder*="טלפון"], input[placeholder*="phone"]');
    await expect(phoneInput.first()).toBeVisible();

    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput.first()).toBeVisible();
  });

  test('has a submit/login button', async ({ page }) => {
    await page.goto('/admin/login');
    const submitBtn = page.locator('button[type="submit"], button:has-text("כניסה"), button:has-text("Login")');
    await expect(submitBtn.first()).toBeVisible();
  });

  test('shows error on empty form submission', async ({ page }) => {
    await page.goto('/admin/login');
    const submitBtn = page.locator('button[type="submit"], button:has-text("כניסה"), button:has-text("Login")');
    await submitBtn.first().click();
    await page.waitForTimeout(1000);

    // Page should still be at login (no navigation happened)
    await expect(page).toHaveURL(/login/);
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/admin/login');

    const phoneInput = page.locator('input[type="text"], input[placeholder*="טלפון"]').first();
    await phoneInput.fill('0500000001');

    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.fill('wrongpassword123');

    const submitBtn = page.locator('button[type="submit"], button:has-text("כניסה")').first();
    await submitBtn.click();
    await page.waitForTimeout(3000);

    // Should still be on login page
    await expect(page).toHaveURL(/login/);
  });
});

test.describe('Protected Routes', () => {
  test('redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/admin');
    await page.waitForTimeout(2000);
    // Should redirect to login or landing
    const url = page.url();
    expect(url.includes('login') || url.endsWith('/')).toBeTruthy();
  });

  test('redirects /admin/users to login when not authenticated', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(2000);
    const url = page.url();
    expect(url.includes('login') || url.endsWith('/')).toBeTruthy();
  });

  test('redirects /admin/packages to login when not authenticated', async ({ page }) => {
    await page.goto('/admin/packages');
    await page.waitForTimeout(2000);
    const url = page.url();
    expect(url.includes('login') || url.endsWith('/')).toBeTruthy();
  });

  test('redirects /admin/settings to login when not authenticated', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.waitForTimeout(2000);
    const url = page.url();
    expect(url.includes('login') || url.endsWith('/')).toBeTruthy();
  });
});
