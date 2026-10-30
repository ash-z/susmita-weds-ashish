// Renders each poster.svg to poster.png beside it (used by poster.py). Playwright's Chromium.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch();
for (const arg of process.argv.slice(2)) {
  const [file, h] = arg.split(':');
  const p = await b.newPage({ viewport: { width: 1080, height: +h }, deviceScaleFactor: 1.5 });
  await p.goto('file://' + file, { waitUntil: 'load' }); await p.waitForTimeout(800);
  await p.screenshot({ path: file.replace(/\.svg$/, '.png'), omitBackground: false });
  await p.close();
}
await b.close();
