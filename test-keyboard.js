const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('https://example.com');
  const tabOrder = [];
  for (let i = 0; i < 25; i++) {
    await page.keyboard.press('Tab');
    const sel = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return 'null';
      return `${el.tagName.toLowerCase()}.${el.className}`.trim();
    });
    tabOrder.push(sel);
  }
  const visibility = await page.evaluate(() => {
    const el = document.activeElement;
    const style = getComputedStyle(el);
    return {
      tag: el ? el.tagName : null,
      outlineStyle: style ? style.outlineStyle : null,
      outlineWidth: style ? style.outlineWidth : null,
    };
  });
  await page.screenshot({ path: '/home/sakthai/tmp/pw-poc/last-focus.png', fullPage: false });
  console.log('TAB_ORDER_JSON', JSON.stringify(tabOrder));
  console.log('FOCUS_VISIBILITY', JSON.stringify(visibility));
  await browser.close();
})();
