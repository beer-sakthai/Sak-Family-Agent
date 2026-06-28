// Headed real-Chrome demo — launches a visible window on this laptop (WSLg).
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    channel: 'chrome',     // real Google Chrome, not bundled chromium
    headless: false,       // show the window
    args: ['--start-maximized'],
  });
  const page = await browser.newPage({ viewport: null });
  await page.goto('https://example.com', { waitUntil: 'domcontentloaded' });
  console.log('OPENED', await page.title());
  await page.waitForTimeout(12000);   // keep window visible ~12s
  await page.screenshot({ path: '/home/sakthai/tmp/pw-poc/headed-chrome.png' });
  await browser.close();
  console.log('SHOWN-DONE');
})();
