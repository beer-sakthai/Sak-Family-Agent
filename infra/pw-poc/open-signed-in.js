// Example "signed-in" run: reuses the persistent profile, so it's already
// logged in. This is the pattern Saksee uses for any signed-in automation.
const { chromium } = require('playwright');

const USER_DATA_DIR = '/home/sakthai/.pw-chrome-profile';
const TARGET = process.argv[2] || 'https://myaccount.google.com/';

(async () => {
  const ctx = await chromium.launchPersistentContext(USER_DATA_DIR, {
    channel: 'chrome',
    headless: false,            // set true for unattended runs
    viewport: null,
    args: ['--start-maximized', '--disable-blink-features=AutomationControlled'],
    ignoreDefaultArgs: ['--enable-automation'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
  console.log('OPENED', await page.title());
  await page.waitForTimeout(10000);
  await page.screenshot({ path: '/home/sakthai/tmp/pw-poc/signed-in.png' });
  await ctx.close();
  console.log('DONE');
})();
