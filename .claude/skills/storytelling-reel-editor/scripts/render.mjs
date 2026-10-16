// Render the compositor page in headless Chrome.
//   node render.mjs <project> stills 4.5 12 20.3      -> <project>/out/stills/ (+ sheet.jpg), with the no-go zones shaded
//   node render.mjs <project> all [workers]          -> <project>/render/00000.jpg ... (every frame)
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const RE_HOME = process.env.REEL_EDITOR_HOME || path.join(os.homedir(), '.reel-editor');
const require = createRequire(path.join(RE_HOME, 'node', 'package.json'));
const puppeteer = require('puppeteer-core');
const { chrome } = JSON.parse(fs.readFileSync(path.join(RE_HOME, 'env.json'), 'utf8'));
const [proj, mode, ...rest] = process.argv.slice(2);
const P = path.resolve(proj);
const meta = JSON.parse(fs.readFileSync(path.join(P, 'project.json'), 'utf8'));
const FPS = meta.fps, total = meta.nframes;
const browsers = [];

async function openPage(extra = '') {
  const browser = await puppeteer.launch({ executablePath: chrome, headless: true,
    args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--hide-scrollbars', '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'] });
  browsers.push(browser);
  const [page] = await browser.pages();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.log('PAGE ERROR:', e.message));
  page.on('console', (m) => { if (m.type() === 'error') console.log('console error:', m.text()); });
  const url = pathToFileURL(path.join(P, 'page', 'index.html')).href + '?frames=' + encodeURIComponent(pathToFileURL(path.join(P, 'frames')).href) + extra;
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(() => window.__ready);
  return page;
}

if (mode === 'stills') {
  const dir = path.join(P, 'out', 'stills');
  fs.mkdirSync(dir, { recursive: true });
  const page = await openPage('&zones=1');
  for (const s of rest) {
    const i = Math.min(total - 1, Math.round(parseFloat(s) * FPS));
    await page.evaluate((i) => window.__frame(i), i);
    await page.screenshot({ path: path.join(dir, `t${parseFloat(s).toFixed(2)}.jpg`), type: 'jpeg', quality: 88 });
  }
  // contact sheet (6 per row) built in Chrome itself
  const files = rest.map((s) => `t${parseFloat(s).toFixed(2)}.jpg`), cols = Math.min(6, files.length), rows = Math.ceil(files.length / cols);
  fs.writeFileSync(path.join(dir, '_sheet.html'), `<body style="margin:0;background:#000;display:grid;grid-template-columns:repeat(${cols},270px)">` +
    files.map((f) => `<div style="position:relative"><img src="${f}" style="width:270px;height:480px;display:block"><b style="position:absolute;left:6px;bottom:6px;color:#ff0;font:16px sans-serif">${f.slice(1, -4)}s</b></div>`).join('') + '</body>');
  await page.setViewport({ width: 270 * cols, height: 480 * rows, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.join(dir, '_sheet.html')).href, { waitUntil: 'load' });
  await page.screenshot({ path: path.join(dir, 'sheet.jpg'), type: 'jpeg', quality: 85 });
  console.log(`${rest.length} stills + sheet.jpg -> ${dir} (red = TikTok/Reels no-go zones; not in the final render)`);
} else if (mode === 'all') {
  const dir = path.join(P, 'render');
  fs.mkdirSync(dir, { recursive: true });
  for (const f of fs.readdirSync(dir)) fs.unlinkSync(path.join(dir, f));
  const workers = Math.max(1, Math.min(parseInt(rest[0] || '0', 10) || Math.max(2, os.cpus().length - 2), 12));
  const per = Math.ceil(total / workers), t0 = Date.now();
  let done = 0;
  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const page = await openPage();
    for (let i = w * per; i < Math.min(total, (w + 1) * per); i++) {
      await page.evaluate((i) => window.__frame(i), i);
      await page.screenshot({ path: path.join(dir, `${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 95 });
      if (++done % 300 === 0) console.log(`${done}/${total} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  }));
  console.log(`rendered ${total} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${dir}`);
} else {
  console.log('usage: node render.mjs <project> stills <t1> <t2> ... | all [workers]');
}
// closing headless Chrome can hang: don't wait more than 5 s
await Promise.race([Promise.all(browsers.map((b) => b.close())), new Promise((r) => setTimeout(r, 5000))]);
process.exit(0);
