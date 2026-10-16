// Safe-area audit: measures every visible overlay and the caption text on EVERY frame.
// Nothing may enter the top 10% / bottom 20% / bottom-right button column (TikTok & Reels UI). Exit code 1 on violations.
//   node safezone.mjs <project>
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const RE_HOME = process.env.REEL_EDITOR_HOME || path.join(os.homedir(), '.reel-editor');
const require = createRequire(path.join(RE_HOME, 'node', 'package.json'));
const puppeteer = require('puppeteer-core');
const { chrome } = JSON.parse(fs.readFileSync(path.join(RE_HOME, 'env.json'), 'utf8'));
const P = path.resolve(process.argv[2]);
const meta = JSON.parse(fs.readFileSync(path.join(P, 'project.json'), 'utf8'));
const Z = JSON.parse(fs.readFileSync(path.join(P, 'style.json'), 'utf8')).safe_area;
const b = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--allow-file-access-from-files'] });
const [p] = await b.pages();
await p.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
await p.goto(pathToFileURL(path.join(P, 'page', 'index.html')).href, { waitUntil: 'load' });
await p.evaluate(() => window.__ready);
const ext = {}, bad = [];
for (let i = 0; i < meta.nframes; i++) {
  const boxes = await p.evaluate(async (i) => {
    await window.__frame(i);
    const out = [];
    document.querySelectorAll('.ui').forEach((el, k) => {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || +cs.opacity < 0.02) return;
      const r = el.getBoundingClientRect(); out.push([el.id || `${el.className.replace('ui ', '')}#${k}`, r.left, r.top, r.right, r.bottom]);
    });
    const cap = document.getElementById('cap');
    if (cap.firstChild) { const rg = document.createRange(); rg.selectNodeContents(cap); const r = rg.getBoundingClientRect(); out.push(['caption', r.left, r.top, r.right, r.bottom]); }
    return out;
  }, i);
  for (const [id, l, t, r, bt] of boxes) {
    const e = ext[id] || (ext[id] = { top: 1e9, bottom: 0, left: 1e9, right: 0 });
    e.top = Math.min(e.top, t); e.bottom = Math.max(e.bottom, bt); e.left = Math.min(e.left, l); e.right = Math.max(e.right, r);
    if (t < Z.top || bt > Z.bottom || (bt > Z.rail_from_y && r > Z.rail_x)) bad.push(`frame ${i} (${(i / meta.fps).toFixed(2)}s) ${id} box [${l.toFixed(0)},${t.toFixed(0)} -> ${r.toFixed(0)},${bt.toFixed(0)}]`);
  }
}
for (const [id, e] of Object.entries(ext)) console.log(id.padEnd(14), `y ${e.top.toFixed(0)}-${e.bottom.toFixed(0)}  x ${e.left.toFixed(0)}-${e.right.toFixed(0)}`);
console.log(bad.length ? `VIOLATIONS: ${bad.length}\n` + bad.slice(0, 20).join('\n') : `SAFE AREA OK: 0 violations across ${meta.nframes} frames`);
await Promise.race([b.close(), new Promise((r) => setTimeout(r, 3000))]);
process.exit(bad.length ? 1 : 0);
