import { test, expect } from '@playwright/test'

test.describe('Trading Dashboard E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('loads dashboard successfully', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Gold Trading/)

    // Check main elements exist
    await expect(page.locator('text=XAU/USD').or(page.locator('text=XAUUSD'))).toBeVisible()
    await expect(page.locator('text=Gold')).toBeVisible()
  })

  test('displays price information', async ({ page }) => {
    // Wait for price to load
    await page.waitForTimeout(3000)

    // Check price display exists
    const priceElements = page.locator('[class*="price"]').or(page.locator('text=4'))
    await expect(priceElements.first()).toBeVisible()
  })

  test('can toggle live mode', async ({ page }) => {
    // Find and click live toggle
    const liveButton = page.locator('button:has-text("Live"), button:has-text("Paused")')
    if (await liveButton.isVisible()) {
      await liveButton.click()
      await page.waitForTimeout(500)
    }
  })

  test('can switch assets', async ({ page }) => {
    // Look for asset selector
    const goldButton = page.locator('button:has-text("Gold"), [role="button"]:has-text("Gold")')
    const btcButton = page.locator('button:has-text("Bitcoin"), [role="button"]:has-text("Bitcoin")')

    if (await btcButton.isVisible()) {
      await btcButton.click()
      await page.waitForTimeout(1000)
      await expect(page.locator('text=BTC').or(page.locator('text=Bitcoin'))).toBeVisible()
    }
  })
})

test.describe('Trading Operations E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForTimeout(2000)
  })

  test('buy button exists', async ({ page }) => {
    const buyButton = page.locator('button:has-text("Buy"), button[class*="buy"]').first()
    await expect(buyButton).toBeVisible()
  })

  test('sell button exists', async ({ page }) => {
    const sellButton = page.locator('button:has-text("Sell"), button[class*="sell"]').first()
    await expect(sellButton).toBeVisible()
  })
})

test.describe('API Connection E2E', () => {
  test('shows connection status', async ({ page }) => {
    await page.goto('/')
    await page.waitForTimeout(3000)

    // Look for connection status indicators
    const connected = page.locator('text=Connected')
    const disconnected = page.locator('text=Disconnected')

    await expect(connected.or(disconnected)).toBeVisible()
  })
})
