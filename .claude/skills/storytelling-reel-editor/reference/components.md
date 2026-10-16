# Components (`page/beats.js`)

`beats.js` runs once when the page loads. Each `BEAT.*` call creates an element and registers how it behaves on every
frame. Times are seconds in the final video; get them from the words.

## Timing helpers

```js
W('getting views')        // start of the first time "getting views" is said
W('this', 25)             // first "this" at or after 25 s (use when a word repeats)
WE('comment Claude')      // END of that phrase
END                       // end of the video
```
Matching ignores case and punctuation; numbers must be written the way Whisper wrote them (check `data/words.json`).
End a graphic 0.04 s before the next beat's word: `until: W('last night') - 0.04`.

## BEAT.notify: iOS notification banner

```js
BEAT.notify({ app: 'tiktok', title: 'TikTok', body: 'Your video is in 300 view jail...', at: W('getting views'), until: W('this clip') - 0.04 });
BEAT.notify({ app: 'stripe', title: 'Stripe', body: 'Someone asked for a refund', at: W('making money'), until: W('this clip') - 0.04 });
```
- 940x124 at x 70, default `top: 270`. Banners with the same `group` (default 'n') stack: each newer one pushes the
  older ones down 148 px with the spring. Two banners occupy y 270-545.
- `app`: `tiktok instagram youtube claude imessage gmail stripe shopify x whatsapp spotify`, or any logo:
  `{ img: 'assets/mylogo.svg', bg: '#FF6243', scale: 70 }`. Unknown names get a letter tile.
- `time` (default 'now').

## BEAT.pill: iOS Focus pill

```js
BEAT.pill({ text: 'Sleep', at: W('while I sleep'), until: W('this clip') - 0.04 });   // moon icon by default; icon: '' for none
```
Centred, 54 px tall, default `top: 200`. Put notifications at 270 when a pill is on screen.

## BEAT.bubble: the app/AI talks back

```js
BEAT.bubble({ app: 'claude', text: 'this mf is restarded these will probably flop lol', sig: '-clanker 5.5',
              at: W('Claude agents'), until: W('last night') - 0.04, top: 509 });
BEAT.bubble({ app: 'claude', text: 'yass bitch im like that', sig: '-clanker 5.5', oneLine: true,
              at: W('entirely'), until: W('getting views') - 0.04, top: 572, left: 156 });
```
- Avatar tile + dark glass bubble (38 px text, 28 px grey signature). Two-line height ≈ 142 px; `oneLine: true`
  puts the signature after the text (≈ 98 px).
- Place it right under the card it answers (card bottom + 14 px), left-aligned with that card.

## BEAT.grid: a card of images or playing clips

```js
BEAT.grid({ app: 'claude', title: '6 ads', sub: 'edited last night',
            items: [1,2,3,4,5,6].map((n) => ({ frames: `assets/ad${n}/`, count: 100 })),   // or { src: 'assets/x.jpg' }
            at: W('six ads'), until: W('getting views') - 0.04 });
BEAT.grid({ app: 'claude', title: 'Claude', sub: 'editing overnight', right: '7 reels', cols: 7, tileW: 112, tileH: 199,
            items: thumbs, at: W('seven fully'), until: W('last night') - 0.04, stagger: 0.04 });
```
- Size = `cols*tileW + gaps + 64` wide, `72 + rows*tileH + gaps + 22` tall; centred unless `left` is given;
  default `top: 200`. 3x2 of 224x126 → 768x360 (y 200-560).
- Tiles pop in staggered (`stagger`, default 0.07 s). `frames` play from the card's entrance at 30 fps
  (`001.jpg`...). Make them from a video:
  `ffmpeg -ss 0.5 -i ad1.mp4 -t 3.4 -vf "fps=30,scale=600:-2" -q:v 3 page/assets/ad1/%03d.jpg`
- 9:16 thumbnails: `tileW: 112, tileH: 199`, up to 7 per row.

## BEAT.comment: "Comment X" call to action

```js
BEAT.comment({ account: 'yourhandle', word: 'Claude', at: W('comment Claude'), typeEnd: WE('comment Claude') + 0.3 });
```
Instagram's dark comment sheet (960x330, default `top: 200`). Types `word` letter by letter between `at` and
`typeEnd` (time it with the creator saying the word), "Post" turns blue, the comment posts as `handle` ("you"), and
the heart fills red a second later. Stays to the end.

## BEAT.card: anything else

```js
// a progress card: 7 reels being edited overnight, each finishing in turn
const tiles = [1,2,3,4,5,6,7].map((n) => `<div class="v" style="width:112px;height:199px"><img src="assets/r${n}.jpg"></div>`).join('');
BEAT.card({
  html: `<div class="hd">${FX.tile('claude', 40, 11)}Claude<span class="sub">editing overnight</span><div class="r"><span class="cnt">0/7</span></div></div>
         <div class="grid" style="left:28px;top:86px;grid-template-columns:repeat(7,112px);gap:18px">${tiles}</div>`,
  at: W('seven fully'), until: W('last night') - 0.04, top: 200, height: 320,
  update: (t, el, k) => {                                  // k = seconds since the card appeared
    const done = Math.min(7, Math.floor(Math.max(0, k - 0.8) / 0.45));
    el.querySelector('.cnt').textContent = `${done}/7`;
    el.querySelectorAll('.v').forEach((v, i) => { v.style.opacity = i < done ? 1 : 0.45; });
  },
});
```
- `FX` has the motion helpers: `FX.spring(t)`, `FX.outCubic(t)`, `FX.clamp(x)`, `FX.tile(app, size, radius)`,
  `FX.MOON`, `FX.setSrc(img, url)` (use it for any image that changes per frame so rendering waits for it).
- `BEAT.custom((t) => { ... })` runs your own function every frame (for anything that isn't a card).

## Layout checklist

1. Find the head top in stills (often y 650-750). Graphics live in y 200 → head top − 20.
2. Card + bubble must fit that band: shrink tiles, use `oneLine`, or drop the header before covering the face.
3. Nothing above y 192, below 1536, or right of 900 below y 960: run `safezone.mjs`.
4. One graphic group at a time; the next appears as the previous leaves.
