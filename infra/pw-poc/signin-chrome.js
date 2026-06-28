// One-time sign-in helper. Opens a real, visible Chrome using a PERSISTENT
// profile dir. Sign in by hand (Google or any site), then CLOSE the window —
// the session is saved to the profile and reused by all later runs.
const { chromium } = require('playwright');

const USER_DATA_DIR = '/home/sakthai/.pw-chrome-profile';

(async () => {
  const ctx = await chromium.launchPersistentContext(USER_DATA_DIR, {
    channel: 'chrome',          // real Google Chrome
    headless: false,            // visible window (WSLg)
    viewport: null,
    args: [
      '--start-maximized',
      // make automated Chrome look normal so Google sign-in isn't blocked
      '--disable-blink-features=AutomationControlled',
    ],
    ignoreDefaultArgs: ['--enable-automation'],
  });

  const page = ctx.pages()[0] || (await ctx.newPage());
  await page.goto('https://accounts.google.com/');
  console.log('SIGNIN-WINDOW-OPEN');
  console.log('-> Sign in in the Chrome window, then close it when done.');

  // Wait until you close the browser window (no timeout).
  await ctx.waitForEvent('close', { timeout: 0 });
  console.log('PROFILE-SAVED at ' + USER_DATA_DIR);
})();
