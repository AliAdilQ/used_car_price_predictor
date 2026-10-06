/* Run against a local seeded Flask app. Optional: BROWSER_PATH, BASE_URL. */
const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');

(async () => {
  const baseURL = process.env.BASE_URL || 'http://127.0.0.1:5000';
  const destination = path.resolve(__dirname, '../docs/screenshots');
  fs.mkdirSync(destination, { recursive: true });
  const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_PATH ? { executablePath: process.env.BROWSER_PATH } : {}) });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1, baseURL });
  try {
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
  const visit = async (url) => {
    const response = await page.goto(url, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, `Failed to load ${url}`);
    await page.evaluate(() => document.fonts.ready);
  };
  const capture = async (filename, fullPage = true) => {
    await page.screenshot({ path: path.join(destination, filename), fullPage, animations: 'disabled' });
    console.log(`Captured ${filename}`);
  };
  await visit('/');
  await capture('home.png');
  await visit('/predict');
  // Verify dependent dropdowns, reference specs, live preview, and reset behavior.
  await page.selectOption('#brand', 'BMW');
  await page.selectOption('#model', 'X3');
  assert.equal(await page.inputValue('#engine'), '2000');
  assert.equal(await page.locator('#preview-car').textContent(), 'BMW X3');
  await page.getByRole('button', { name: 'Reset details' }).click();
  assert.equal(await page.inputValue('#brand'), 'Toyota');
  assert.equal(await page.inputValue('#model'), 'Corolla');
  await capture('predict.png');
  await page.getByRole('button', { name: /Estimate my car/ }).click();
  await page.waitForURL('**/result/**');
  const resultPath = new URL(page.url()).pathname;
  assert.match(await page.locator('.price-amount').textContent(), /\$[\d,]+\s+USD/);
  await capture('result.png');
  await visit('/admin/login');
  await capture('admin-login.png');
  await page.fill('#username', process.env.ADMIN_USERNAME || 'admin');
  await page.fill('#password', process.env.ADMIN_PASSWORD || 'Admin@123');
  await page.getByRole('button', { name: 'Sign in to workspace' }).click();
  await page.waitForURL('**/admin/');
  await page.waitForFunction(() => typeof Chart !== 'undefined' && Chart.getChart('activity-chart'));
  await page.waitForTimeout(900);
  await capture('admin-dashboard.png');
  await visit('/admin/predictions');
  await capture('prediction-history.png');
  await page.fill('input[name=q]', 'Toyota');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await page.waitForURL('**/admin/predictions?**');
  assert.match(await page.locator('tbody').textContent(), /Toyota/);
  await visit('/admin/dataset');
  await capture('dataset.png');
  await visit('/about');
  await capture('about.png');
  // Small-screen verification covers every main layout, plus real screenshots.
  await page.setViewportSize({ width: 390, height: 844 });
  for (const [url, name] of [['/', 'mobile-home.png'], ['/predict', 'mobile-predict.png'], [resultPath, 'mobile-result.png'], ['/admin/', 'mobile-dashboard.png'], ['/admin/predictions', 'mobile-history.png'], ['/admin/dataset', 'mobile-dataset.png'], ['/about', 'mobile-about.png']]) {
    await visit(url);
    const layout = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > window.innerWidth,
      offenders: [...document.querySelectorAll('body *')].filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1 && (!element.closest('.table-responsive') || element.classList.contains('table-responsive'))).map((element) => `${element.tagName}.${element.className}`).slice(0, 10),
      tables: [...document.querySelectorAll('.table-responsive')].map(element => ({width:element.getBoundingClientRect().width, right:element.getBoundingClientRect().right, overflow:getComputedStyle(element).overflowX, scroll:element.scrollWidth})),
      documentWidth: document.documentElement.scrollWidth,
    }));
    if (layout.overflow) console.log(JSON.stringify(layout));
    assert.equal(layout.overflow, false, `Horizontal overflow: ${url}: ${layout.offenders.join(', ')}`);
    if (name) await capture(name);
  }
  await visit('/');
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await page.locator('#main-nav').getByRole('link', { name: 'Price predictor' }).click();
  await page.waitForURL('**/predict');
  assert.equal(await page.inputValue('#model'), 'Corolla');
  assert.deepEqual(errors, [], 'Browser errors detected');
  fs.writeFileSync(path.join(destination, 'verification.json'), JSON.stringify({ viewport: '1440 × 1000', mobile: '390 × 844', browserErrors: errors, verified: ['public prediction', 'brand/model dependencies', 'reset', 'admin login', 'charts', 'history search', 'dataset', 'mobile overflow', 'mobile navigation'] }, null, 2) + '\n');
  console.log('Browser flows and mobile layouts passed.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
