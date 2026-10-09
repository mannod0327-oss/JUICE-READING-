// Every standalone page in a real Chromium: loads clean, pictures decode, answering with the key gives 100 %,
// a blank paper gives 0 %, nothing scrolls sideways on a 390 px phone, and (with the audio pack) every player loads.
//   node tests/site.e2e.mjs SITE_DIR OUT_DIR
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const [site, out] = process.argv.slice(2);
const pages = fs.readdirSync(site).filter((f) => /^jr\d-(u\d\d|vc\d|mid|fin)\.html$/.test(f)).sort();
const browser = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {});
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
let failed = 0, audioChecked = 0;
for (const f of pages.concat(['index.html'])) {
  const page = await ctx.newPage(), errors = [];
  page.on('console', (m) => { if (m.type() === 'error' && !/audio\//.test(m.text()) && !/ERR_FILE_NOT_FOUND/.test(m.text())) errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto('file://' + path.resolve(site, f));
  const fail = (m) => { failed++; console.log(`  ✗ ${f}: ${m}`); };
  const wide = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (wide > 1) fail(`horizontal scroll ${wide}px`);
  const broken = await page.evaluate(() => [...document.images].filter((i) => !i.complete || !i.naturalWidth).length);
  if (broken) fail(`${broken} pictures did not decode`);
  // when the audio pack is in place (npm run audio), both players must load a real track
  if (fs.existsSync(path.join(site, 'audio', 'jr1-u01.mp3'))) {
    const audio = await page.evaluate(() => Promise.all([...document.querySelectorAll('audio')].map((a) => new Promise((ok) => {
      if (a.readyState >= 1) return ok(a.duration);
      a.addEventListener('loadedmetadata', () => ok(a.duration)); a.addEventListener('error', () => ok(-1)); a.load();
    }))));
    if (audio.some((d) => !(d > 5))) fail(`audio did not load: ${JSON.stringify(audio)}`);
    if (/^jr\d-u\d\d\.html$/.test(f) && audio.length !== 2) fail(`expected 2 players (passage + words), got ${audio.length}`);
    audioChecked += audio.length;
  }
  if (f !== 'index.html') {
    const r = JSON.parse(fs.readFileSync(path.join(out, 'units', f.replace('.html', '').toUpperCase() + '.json'), 'utf8'));
    await page.click('button[type=submit]');
    const zero = await page.textContent('#result .score');
    if (!/^0 \/ \d+ · 0%$/.test(zero.trim())) fail(`blank paper scored "${zero}"`);
    await page.click('#again');
    for (const q of r.content.questions) {
      const k = r.answer_key.items[q.id];
      if (q.type === 'text') await page.fill(`input[name="${q.id}"]`, k.t[0]);
      else await page.check(`input[name="${q.id}"][value="${k.a}"]`);
    }
    await page.click('button[type=submit]');
    const full = (await page.textContent('#result .score')).trim();
    const bad = await page.locator('.q.is-bad').count();
    if (full !== `${r.content.questions.length} / ${r.content.questions.length} · 100%` || bad) fail(`key scored "${full}", ${bad} marked wrong`);
  }
  if (errors.length) fail(`console: ${errors.join(' | ')}`);
  await page.close();
}
await browser.close();
console.log(`${pages.length + 1} pages, ${audioChecked} audio players loaded, ${failed} failures`);
process.exit(failed ? 1 : 0);
