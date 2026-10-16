import { execFileSync } from 'node:child_process'

import { expect, test, type Page } from '@playwright/test'

const PASSWORD = 'super-secret-1'

function uniqueEmail(): string {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`
}

// Same SQL the UI shows on 403, run against the compose database
function grantAdmin(email: string): void {
  const sql =
    "INSERT INTO user_permissions (user_id, permission, updated_at) " +
    `SELECT id, 'admin', now() FROM users WHERE email = '${email}'`
  execFileSync('docker', ['compose', 'exec', '-T', 'db', 'psql', '-U', 'postgres', '-c', sql], { cwd: '..' })
}

async function register(page: Page, email: string): Promise<void> {
  await page.goto('/register')
  await page.getByLabel('First name').fill('E2E')
  await page.getByLabel('Last name').fill('Tester')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page).toHaveURL(/\/profile$/)
}

test('register, browse data as admin and log out', async ({ page }) => {
  const email = uniqueEmail()
  await register(page, email)
  await expect(page.getByRole('heading', { name: 'E2E Tester' })).toBeVisible()
  await expect(page.getByText(email)).toBeVisible()

  await page.getByRole('link', { name: 'Data' }).click()
  await expect(page.getByText('does not have the admin permission')).toBeVisible()

  grantAdmin(email)
  await page.reload()
  await expect(page.getByRole('table')).toBeVisible()

  await page.getByLabel('email', { exact: true }).fill(email)
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.getByText(/^1 row ·/)).toBeVisible()
  await expect(page.getByRole('cell', { name: 'password' })).toHaveCount(0)

  await page.getByRole('cell', { name: email }).click()
  await expect(page.getByRole('complementary', { name: 'Row detail' })).toContainText(email)

  await page.getByLabel('Model').selectOption('user-permissions')
  await expect(page.getByRole('columnheader', { name: /^permission/ })).toBeVisible()

  await page.getByRole('button', { name: 'Log out' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await page.goto('/profile')
  await expect(page).toHaveURL(/\/login$/)
})

test('shows the API error message and trace id', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill(uniqueEmail())
  await page.getByLabel('Password').fill('wrong-password')
  await page.getByRole('button', { name: 'Log in' }).click()

  const alert = page.getByRole('alert')
  await expect(alert).toContainText('email or password is invalid')
  await expect(alert).toContainText('users-002')
})

test('refreshes an invalid access token automatically', async ({ page }) => {
  const email = uniqueEmail()
  await register(page, email)

  // Break the access token but keep the refresh token, then reload
  await page.evaluate(() => {
    const tokens = JSON.parse(localStorage.getItem('auth.tokens') ?? '{}')
    localStorage.setItem('auth.tokens', JSON.stringify({ ...tokens, access: 'invalid' }))
  })
  await page.reload()

  await expect(page.getByText(email)).toBeVisible()
  const access = await page.evaluate(() => JSON.parse(localStorage.getItem('auth.tokens') ?? '{}').access)
  expect(access).not.toBe('invalid')
})
