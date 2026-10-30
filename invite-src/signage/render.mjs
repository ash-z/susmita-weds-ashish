// render each sign to a PNG preview (150 dpi, trimmed) and a print PDF (trim size plus bleed):  node render.mjs DIR name ...
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [dir, ...names] = process.argv.slice(2);
for (const name of names) {               // a fresh browser each time: big captures fail in a reused one
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 1.5 });
  await p.goto(`file://${dir}/${name}.html`); await p.evaluate(() => document.fonts.ready);
  const page = await p.evaluate(() => [document.body.offsetWidth, document.body.offsetHeight]);
  await p.setViewportSize({ width: page[0], height: page[1] }); await p.waitForTimeout(300);
  const t = await p.evaluate(() => { const r = document.getElementById('trim').getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; });
  await p.screenshot({ path: `${dir}/${name}.png`, clip: t });
  await p.pdf({ path: `${dir}/${name}.pdf`, width: `${page[0] / 100}in`, height: `${page[1] / 100}in`, printBackground: true, pageRanges: '1' });
  await b.close(); console.log('rendered', name);
}
