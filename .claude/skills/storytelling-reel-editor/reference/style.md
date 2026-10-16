# The style, and why

Every rule here came out of real revisions on posted reels. When the creator you're working with disagrees, they win:
change `style.json` and log it in `MY_STYLE.md`.

## Captions

| Setting | Value | Why |
|---|---|---|
| Font | TikTok Sans (SIL OFL, bundled) | Reads as native to the platform; viewers trust it as "the app's own" text |
| Weight | 600 | 500-550 looked thin on a phone over busy footage. Note: TikTok Sans in 50-step jumps changes ink by only ~5%, so a change from 500 to 550 is nearly invisible. Make weight changes in steps of 50-100 and show a crop |
| Size | 56 px on 1080 wide | One step smaller than typical (64 px): the face stays the focus |
| Letter spacing | -0.035em | Default spacing looked loose and "off-brand"; tighter spacing read as the TikTok-native look |
| Colour | #fff only | No highlight words, no colour pops: the voice carries the emphasis |
| Effects | none | No shadow, outline, box, pop, bounce or karaoke. Hard cut on, hard cut off |
| Chunks | 2-3 words, cut on phrases | Readable at a glance; never end a chunk on "the/to/and/while"; keep numbers with their noun |
| Case | Sentence case as spoken | Feels like speech, not a slide. Proper nouns capitalised (TikTok, Claude) |
| Position | centre y 1055 | A fixed reading spot near the mouth. Over the face is fine for text this light |
| Timing | on at the first word −40 ms, off at the next chunk (or +0.5 s before a pause) | |

Swears are starred in captions only; the audio stays. Fix misheard words in `captions.json` and tell the creator
which words you guessed.

## Safe area (TikTok / Reels UI)

On a 1080x1920 frame:
- **Top 10%: y 0-192**: For You / Following tabs, the Reels header, search, LIVE.
- **Bottom 20%: y 1536-1920**: username, caption text, the sound line, the nav bar.
- **Bottom-right column: x 900-1080 from y 960 down**: avatar, like, comment, save, share, the sound disc.

Nothing you add may touch these, at any frame, including mid-animation (springs overshoot, stacked notifications
push down). `safezone.mjs` measures every element on every frame. Footage the creator filmed (text they burned in
while recording) is theirs; leave it.

Usable area: y 192-960 full width (above the head, the graphics zone), and y 960-1536 left of x 900 (captions).

## Graphics

**What to show.** The literal thing being said, as the app it lives in: "getting views" → a TikTok notification;
"six ads" → a grid of the six ads playing; "comment X" → an Instagram comment sheet typing X. Concrete beats abstract.
Real logos and real screens trigger recognition; generic shapes don't.

**Where.** Above the head, in the band y 200 to the top of the hair (find it in stills; often y 650-750). If a card
plus a bubble don't fit, shrink the card (smaller tiles) or put the bubble's signature on one line, never cover the
face. Centre narrow cards.

**When.** In on the first word of the phrase that names it (never early), out when the next idea starts. Text needs
≥ 2 s on screen; a joke bubble 2-4 s. It's fine to hold a card through the next sentence if it keeps the joke on
screen ("This is insane, dude" under "these will probably flop lol").

**How it moves.** One motion vocabulary: the Apple-style spring pop in, a short fade-scale out over 0.18 s.
Inner items stagger 0.04-0.07 s. Notifications stack like iOS: a new one pushes the older ones down. No spins,
slides across the screen, or slow fades.

**How it looks.** Dark glass cards (rgba(20,20,24,.62), 26 px blur, 34 px radius); iOS banners (light frosted, 32 px
radius, app tile, "now"); the Focus pill (Sleep, Do Not Disturb); Instagram's dark comment sheet. System font for UI
text, TikTok Sans only for captions. No emojis anywhere: use logos and UI instead.

**Humour.** The UI is where the joke lives. Two patterns that land:
- The tool talks back: a bubble from the AI/app with a sassy line and a sign-off ("this mf is restarded these will
  probably flop lol / -clanker 5.5", then later "yass bitch im like that").
- The UI undercuts the brag: while the creator says "getting views and making money while I sleep", the phone shows
  "Your video is in 300 view jail..." and "Someone asked for a refund".
Use the creator's own words for jokes, verbatim (their spelling too).

**Honesty.** Use real screenshots and numbers when you have them. Anything illustrative must not look like a real
receipt for a specific person or business. Never invent payment amounts, follower counts or testimonials.

## Audio

- Original audio at 200% (+6 dB): creator clips are usually quiet; 200% lands around -11 LUFS. Some creators go to
  300%: ask once, then store it in `style.json`.
- Music at 10% under speech. During a quiet intro (before the drums/vocals), 25%, because the intro alone is much
  quieter and 10% disappears; at the drum entrance songs jump 4-6 dB and 25% would fight the voice. The level steps
  down in 30 ms right before the first kick, so the drum hit hides the change.
- Sound effects: the hit lands on the word's onset at about speech level (-7 dB for a typical vine boom). Classic use:
  the reveal / fourth-wall line ("this video was edited by Claude" → boom on "Claude").
- The music stops on the boom (30 ms fade ending on the hit): silence after a boom is funnier than music carrying on.
- Final: limiter at -1 dB with latency compensation; verify sync = 0 samples against the source.
