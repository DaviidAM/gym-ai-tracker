import { test, expect } from '@playwright/test';

/**
 * GymAI Tracker — Extended E2E Playwright Tests
 * Tests: Auth (register, login, logout), Chat, Analytics
 *
 * Prerequisites:
 *   - Frontend dev server running at http://localhost:4321
 *   - Backend API server running at http://localhost:8000
 *
 * Run from /root/Hermes/repos/gym-ai-tracker:
 *   npx playwright test tests/e2e/extended.spec.ts
 */

const BASE_URL = 'http://localhost:4321';
const API_BASE = 'http://localhost:8000';

// ─── Auth Tests ───────────────────────────────────────────────────────────────

test.describe('Auth', () => {

  test('register page loads with correct elements', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/register`);
    await expect(page.locator('main h1')).toContainText('Create Account');
    await expect(page.locator('main #email')).toBeVisible();
    await expect(page.locator('main #username')).toBeVisible();
    await expect(page.locator('main #password')).toBeVisible();
    await expect(page.locator('main button[type="submit"]')).toContainText('Create Account');
    await expect(page.locator('main a[href="/auth/login"]')).toBeVisible();
  });

  test('login page loads with correct elements', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await expect(page.locator('main h1')).toContainText('Welcome Back');
    await expect(page.locator('main #username')).toBeVisible();
    await expect(page.locator('main #password')).toBeVisible();
    await expect(page.locator('main button[type="submit"]')).toContainText('Sign In');
    await expect(page.locator('main a[href="/auth/register"]')).toBeVisible();
  });

  test('register a new user successfully', async ({ page }) => {
    const random = Date.now();
    const email = `testuser${random}@example.com`;
    const username = `testuser${random}`;
    const password = 'testpassword123';

    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('#email', email);
    await page.fill('#username', username);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');

    // Should show success and redirect
    const successDiv = page.locator('#register-success');
    await expect(successDiv).toBeVisible({ timeout: 5000 });
    await expect(successDiv).toContainText('Account created');

    // Should redirect to login after success
    await page.waitForURL(/\/auth\/login/, { timeout: 5000 });
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('register fails with duplicate email', async ({ page }) => {
    // First register a user
    const random = Date.now();
    const email = `duptest${random}@example.com`;
    const username1 = `user1_${random}`;
    const username2 = `user2_${random}`;
    const password = 'testpassword123';

    // Register first user
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('#email', email);
    await page.fill('#username', username1);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/auth\/login/, { timeout: 5000 });

    // Try to register with same email but different username
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('#email', email);
    await page.fill('#username', username2);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');

    const errorDiv = page.locator('#register-error');
    await expect(errorDiv).toBeVisible({ timeout: 5000 });
    await expect(errorDiv).toContainText('Email already registered');
  });

  test('login with valid credentials works', async ({ page }) => {
    // First register a user
    const random = Date.now();
    const email = `logintest${random}@example.com`;
    const username = `logintest${random}`;
    const password = 'testpassword123';

    // Register
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('#email', email);
    await page.fill('#username', username);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/auth\/login/, { timeout: 5000 });

    // Login with same credentials
    await page.fill('#username', username);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 5000 });
    await expect(page).toHaveURL(/\/dashboard/);

    // User should be stored in sessionStorage
    const stored = await page.evaluate(() => sessionStorage.getItem('gymai_user'));
    expect(stored).not.toBeNull();
    const user = JSON.parse(stored!);
    expect(user.username).toBe(username);
  });

  test('login fails with wrong password', async ({ page }) => {
    const random = Date.now();
    const email = `wrongpw${random}@example.com`;
    const username = `wrongpw${random}`;
    const password = 'correctpassword';
    const wrongPassword = 'wrongpassword';

    // Register
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('#email', email);
    await page.fill('#username', username);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/auth\/login/, { timeout: 5000 });

    // Try to login with wrong password
    await page.fill('#username', username);
    await page.fill('#password', wrongPassword);
    await page.click('button[type="submit"]');

    const errorDiv = page.locator('#login-error');
    await expect(errorDiv).toBeVisible({ timeout: 5000 });
    await expect(errorDiv).toContainText('Invalid username or password');
  });

  test('login fails with non-existent user', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('#username', 'nonexistent_user_12345');
    await page.fill('#password', 'somepassword');
    await page.click('button[type="submit"]');

    const errorDiv = page.locator('#login-error');
    await expect(errorDiv).toBeVisible({ timeout: 5000 });
    await expect(errorDiv).toContainText('Invalid username or password');
  });

});

// ─── Chat Tests ────────────────────────────────────────────────────────────────

test.describe('Chat', () => {

  test('chat page loads with input field and send button', async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
    await expect(page.locator('h1')).toContainText('AI Coach Chat');
    await expect(page.locator('#chat-input')).toBeVisible();
    await expect(page.locator('#chat-form button[type="submit"]')).toBeVisible();
    await expect(page.locator('#chat-messages')).toBeVisible();
  });

  test('chat shows welcome message from AI', async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
    const messages = page.locator('#chat-messages');
    await expect(messages.locator('text=AI coach')).toBeVisible({ timeout: 3000 });
  });

  test('user can type and send a message', async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
    await page.fill('#chat-input', 'What is the best bicep exercise?');
    await page.click('#chat-form button[type="submit"]');

    // User message should appear
    const messages = page.locator('#chat-messages');
    await expect(messages.locator('text=What is the best bicep exercise?')).toBeVisible({ timeout: 3000 });

    // Wait for AI response (simulated)
    await page.waitForTimeout(1000);
    // The demo AI response should appear
    await expect(messages.locator('text=This is a demo')).toBeVisible({ timeout: 5000 });
  });

  test('chat does not submit empty messages', async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
    const messagesCountBefore = await page.locator('#chat-messages .flex').count();

    // Try to submit empty input
    await page.click('#chat-form button[type="submit"]');

    // Message count should not increase
    await page.waitForTimeout(500);
    const messagesCountAfter = await page.locator('#chat-messages .flex').count();
    expect(messagesCountAfter).toBe(messagesCountBefore);
  });

});

// ─── Analytics Tests ──────────────────────────────────────────────────────────

test.describe('Analytics', () => {

  test('analytics page loads and shows HTMX summary', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);
    await expect(page.locator('main h1')).toContainText('Analytics');

    // Wait for HTMX to load summary
    const summary = page.locator('#analytics-summary');
    await expect(summary).toBeVisible({ timeout: 5000 });

    // Summary should load stats (total workouts, this week, etc.)
    await expect(summary.locator('text=Total Workouts')).toBeVisible({ timeout: 5000 });
  });

  test('analytics /volume endpoint returns JSON', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/analytics/volume`);
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test('analytics /progression endpoint requires exercise_id', async ({ page }) => {
    // Without exercise_id, should return 422 or similar validation error
    const response = await page.request.get(`${API_BASE}/analytics/progression`);
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });

  test('analytics /frequency endpoint returns JSON', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/analytics/frequency`);
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test('analytics /summary endpoint returns HTML', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/analytics/summary`);
    expect(response.ok()).toBe(true);
    const text = await response.text();
    expect(text).toContain('Total Workouts');
    expect(text).toContain('This Week');
  });

  test('analytics /exercises endpoint returns exercises list', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/analytics/exercises`);
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

});

// ─── API Auth Tests ───────────────────────────────────────────────────────────

test.describe('Auth API', () => {

  test('POST /auth/register creates user', async ({ page }) => {
    const random = Date.now();
    const response = await page.request.fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: JSON.stringify({
        email: `apitest${random}@example.com`,
        username: `apitest${random}`,
        password: 'apipassword123',
      }),
    });
    expect(response.ok()).toBe(true);
    const user = await response.json();
    expect(user.username).toBe(`apitest${random}`);
    expect(user.email).toBe(`apitest${random}@example.com`);
  });

  test('POST /auth/login returns user on valid credentials', async ({ page }) => {
    const random = Date.now();
    const username = `logintestapi${random}`;
    const password = 'testpass123';

    // Register
    await page.request.fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: JSON.stringify({
        email: `${username}@example.com`,
        username,
        password,
      }),
    });

    // Login
    const response = await page.request.fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: new URLSearchParams({ username, password }).toString(),
    });
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(data.username).toBe(username);
    expect(data.id).toBeDefined();
  });

  test('POST /auth/logout returns success', async ({ page }) => {
    const response = await page.request.fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
    });
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(data.message).toBe('Logged out');
  });

});
