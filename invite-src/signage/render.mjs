// render each sign to PNG (150 dpi) and a print PDF (24 x 36 in, text as vectors):  node render.mjs DIR name ...
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [dir, ...names] = process.argv.slice(2);
const b = await chromium.launch();
for (const name of names) {
  const p = await b.newPage({ viewport: { width: 2400, height: 3600 }, deviceScaleFactor: 1.5 });
  await p.goto(`file://${dir}/${name}.html`); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
  await p.screenshot({ path: `${dir}/${name}.png` });
  await p.pdf({ path: `${dir}/${name}.pdf`, width: '24in', height: '36in', printBackground: true, pageRanges: '1' });
  await p.close(); console.log('rendered', name);
}
await b.close();
