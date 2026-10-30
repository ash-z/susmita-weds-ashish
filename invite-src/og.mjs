// Render the link-preview image (docs/og.jpg source) from the opening screen.
// Usage: node og.mjs <path-to-built-index.html> <out.png>
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [src, out] = process.argv.slice(2);
const b = await chromium.launch({ args:['--use-gl=swiftshader','--enable-unsafe-swiftshader'] });
const ctx = await b.newContext({ viewport:{width:1200,height:630}, ignoreHTTPSErrors:true });
const p = await ctx.newPage();
let ok = false;
for (let attempt = 1; attempt <= 4 && !ok; attempt++){
  await p.goto('file://' + src, { waitUntil:'networkidle' });
  ok = await p.evaluate(async()=>{
    try{
      await Promise.all([document.fonts.load('60px "Alex Brush"'), document.fonts.load('40px "Tiro Telugu"'), document.fonts.load('20px Marcellus'),
                         document.fonts.load('20px "Noto Sans Telugu"', 'శుభలేఖ')]);
      await document.fonts.ready;
    }catch(e){}
    const loaded = fam => [...document.fonts].some(f => f.family.replace(/"/g,'') === fam && f.status === 'loaded');
    return loaded('Alex Brush') && loaded('Tiro Telugu') && loaded('Marcellus') && loaded('Noto Sans Telugu');
  });
  console.log('attempt', attempt, 'fonts loaded:', ok);
}
if (!ok) { console.error('Fonts never loaded; refusing to write a fallback-font preview.'); process.exit(1); }
// a wide composition for link previews: the couple on the left, names on the right
await p.addStyleTag({ content:`
  .open-btn,.pal,.sp-corner{display:none!important}
  .sp-inner{display:grid!important;grid-template-columns:auto auto;column-gap:64px;row-gap:12px;align-items:center;justify-items:center;max-width:none!important;padding-top:104px!important}
  .sp-inner .seal{grid-column:1;grid-row:1/5;width:250px!important;margin:0 0 20px!important}
  .sp-inner .invocation{grid-column:2;grid-row:1}
  .sp-inner .eyebrow{grid-column:2;grid-row:2}
  .sp-names{grid-column:2;grid-row:3}
  .sp-date{grid-column:2;grid-row:4}
  .crown .toranam{width:820px!important}
  .crown .ganesha{width:56px!important;top:22px!important}` });
await p.waitForTimeout(2400);
await p.screenshot({ path: out });
await b.close();
