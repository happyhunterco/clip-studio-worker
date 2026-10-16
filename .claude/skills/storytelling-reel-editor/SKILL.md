---
name: storytelling-reel-editor
description: Edit a talking-head vertical video (Instagram Reel, TikTok, YouTube Short) in a clean storytelling style. Adds TikTok Sans auto-captions (2-3 words, white, no effects), simple iOS-style UI pop-ups above the speaker's head timed to their words (notifications, cards, an AI or app "talking back", a comment-CTA sheet), keeps everything out of the TikTok/Reels button zones, mixes faint background music that drops when the drums kick in, and lands meme sound effects on a word. Use whenever someone asks to caption, edit or "make this a reel" from a talking video file.
---

# Storytelling reel editor

Turns a raw talking-to-camera clip into a finished 1080x1920 reel: captions, a few simple animated UI moments, music and
sound effects. Built by Mino Lee (@minolee.mp4) from the edits Mino actually posts. The look is deliberately simple:
the person talking stays the star, and every graphic earns its place by showing exactly what they are saying.

Paths below: `$SKILL` = this skill's folder, `$PY` = `~/.reel-editor/venv/bin/python -I`, `$P` = the project folder.

## The style (follow it unless the creator says otherwise)

1. **Captions**: TikTok Sans, weight 600, 56 px on a 1080-wide frame, letter spacing -0.035em, pure white. No
   shadow, no outline, no box, no animation: each 2-3 word chunk hard-cuts on and off. Sentence case exactly as
   spoken; swears starred ("f*cking"). One line, centred, vertical centre at y 1055 (55% down, around the mouth).
2. **Safe area**: nothing (no caption, card or sticker) in the top 10% (y < 192), the bottom 20% (y > 1536) or the
   bottom-right button column (x > 900 below y 960). That is where TikTok and Reels draw their own UI.
3. **Keep it simple**: no zooms, cuts, B-roll, emojis or effects unless asked. Add a graphic only where the creator
   asks for one, or (when they want suggestions) where a line names something concrete you can show. One idea per
   graphic.
4. **Graphics look like real apps** (familiarity beats decoration): iOS notification banners, dark glass cards,
   real app logos, an Instagram comment sheet for "Comment X" calls to action. They sit **above the person's head**,
   never on the face.
5. **Timed to the words**: a graphic pops in on the first word of the phrase that names it (Apple-style spring:
   fade 0.12 s, scale .92 → 1, 22 px rise) and leaves when the next idea starts. Hold anything with text ≥ 2 s.
6. **Humour lands in the UI**: the app or AI can "talk back" in a bubble (`-clanker 5.5` style sign-off), and
   notifications can undercut the brag ("getting views..." → "Your video is in 300 view jail..."). Use the
   creator's exact words for jokes.
7. **Audio**: the clip's own audio at 200% (2x, the creator can ask for up to 300%). Background music at 25% while the
   song is still in its quiet intro, then 10% from the moment the drums or vocals kick in (songs get distractingly
   loud there). A meme sound effect (vine boom...) lands on the exact word; the music stops on it. Limit at -1 dB.
8. **Prove what you claim**: report exact numbers (font weight, sizes, levels, times) and back visual claims with
   evidence (stills, the safe-area audit, measured loudness). If the creator doubts something, measure it and show it.

All of these numbers live in `$SKILL/style.json`. Details and the reasons behind them: `reference/style.md`.

## Workflow

**0. Setup (once per computer).** Run `bash $SKILL/scripts/setup.sh`. It checks ffmpeg, Node, Python and Chrome
(printing install commands for anything missing) and installs Whisper and puppeteer-core into `~/.reel-editor/`.
The first transcription downloads the Whisper model (~1.5 GB).

**1. Intake.** Get the clip path. Ask only what you can't infer, in one message: which moments should get a graphic
(or "suggest some"), the music file if any (and where in the song to start), sound effects and where, the
creator's @handle for the comment CTA. Don't block on optional things: no music = voice only.

**2. Project.** `$PY $SKILL/scripts/new_project.py <clip>` creates `<clip>-edit/` next to the clip: 30 fps
1080x1920 frames, 16 kHz audio, the page template, a copy of `style.json`. Read its warnings (not 9:16, HDR, no
audio) and tell the creator about any.

**3. Transcribe.** `$PY $SKILL/scripts/transcribe.py $P --prompt "names, brands, slang in the video"`. Read the
transcript carefully: Whisper mishears names, drops/invents words at the end ("...skill hole"), and writes numbers
inconsistently. Fix in step 4, never by editing words.json timing.

**4. Captions.** Write `$P/captions.json` if needed (`replace`, `phrase_replace`, `remove`, `overrides`,
`breaks_before`, `hide`; documented at the top of `scripts/captions.py`), then `$PY $SKILL/scripts/captions.py $P`.
Read every chunk it prints: no chunk should split a phrase awkwardly ("I should wake | up with six") or end on a
weak word; fix with `overrides` (anchored on the words, so they survive edits). Flag any word you guessed.

**5. Beat plan.** Write a short table: time → spoken line → graphic → why. Look at stills of those moments first so
you know where the head is. Share the plan before building when the creator asked for several graphics or for
suggestions.

**6. Build.** Write `$P/page/beats.js` with the `BEAT` helpers (`reference/components.md`): `notify`, `pill`,
`bubble`, `grid`, `comment`, `card`, `custom`. Time everything with `W('phrase')` (start of a spoken phrase) and
`WE('phrase')` (its end). Put images in `$P/page/assets/`. Use real logos/screens/frames whenever the creator has
them; make example numbers obviously illustrative.

**7. Check before rendering.**
- `node $SKILL/scripts/render.mjs $P stills <t1> <t2> ...` (one still per beat + a few captions only). Open
  `$P/out/stills/sheet.jpg`: graphics above the head, text readable at phone size, nothing in the red zones.
- `node $SKILL/scripts/safezone.mjs $P` must print `SAFE AREA OK` (it measures every element on every frame).

**8. Render.** `node $SKILL/scripts/render.mjs $P all` (≈20 s per 40 s of video on a laptop).

**9. Audio.** `$PY $SKILL/scripts/mix_audio.py $P [--music song.m4a] [--music-start 0] [--drums auto|SEC|none]
[--sfx boom.mp3@SEC] [--cut-music-at-sfx]`. SEC for a sound effect = the word's time from `data/words.json`; the
script snaps it to the word's real onset. It prints where the drums were detected: sanity-check it (listen or ask)
and override with `--drums SEC` if the song has a quiet intro with vocals. It must report sync 0. See
`reference/audio.md`.

**10. Encode + QA.** `bash $SKILL/scripts/encode.sh $P $P/out/<name>-v1.mp4`, then
`$PY $SKILL/scripts/check.py $P $P/out/<name>-v1.mp4 <beat times>` and look at `$P/out/check.jpg`.

**11. Deliver.** Give the file and a short summary: what's on screen and when, caption settings (weight 600, 56 px,
-0.035em), audio levels, anything you guessed (a misheard word, an illustrative number), and that nothing touches
the TikTok/Reels UI. Keep every version (`-v1`, `-v2`...): never overwrite a delivered file.

## Revisions

Creators iterate by feel ("slightly smaller", "it doesn't look bolder"). Change one thing at a time, by a small
step, and show a before/after crop for type changes. When a change is a preference ("always", "remember this",
"make that the default"), save it: edit `$SKILL/style.json` (or the relevant rule here) and add a dated line to
`$SKILL/MY_STYLE.md` with their exact words, so every future edit starts from it.

## Troubleshooting

- `MISSING:` from setup: install what it names, rerun.
- HDR clip error: export SDR from the editor app (CapCut: HDR off; iPhone: share → Options → Most Compatible).
- Fonts look wrong in stills: the page must load `page/fonts/TikTokSans-latin.woff2` (new_project copies it).
- `W(): "..." not found`: the phrase must match the transcript words (check `data/words.json`; contractions and
  numbers are written the way Whisper wrote them).
- Render hangs: close other Chrome-heavy apps or pass fewer workers (`render.mjs $P all 4`).
- Sync error from mix_audio: never deliver; rerun (it compensates the limiter's delay with `latency=1`).
