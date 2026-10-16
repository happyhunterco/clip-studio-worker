# Audio

`mix_audio.py` builds `out/mix.wav` from the clip's own audio, optional music and sound effects, then verifies it.

```bash
$PY $SKILL/scripts/mix_audio.py $P                                   # voice only, 200%
$PY $SKILL/scripts/mix_audio.py $P --music song.m4a                  # + music, drums auto-detected
$PY $SKILL/scripts/mix_audio.py $P --music song.m4a --music-start 31.5 --drums none
$PY $SKILL/scripts/mix_audio.py $P --music song.m4a --sfx vine-boom.mp3@38.34 --cut-music-at-sfx
```

## Levels (from `style.json` → `audio`)

| | Default | Override |
|---|---|---|
| Original audio | 2.0 (200%) | `--voice-gain 3.0` |
| Music, quiet intro (before drums/vocals) | 0.25 | `--intro-gain` |
| Music, after the drums kick in | 0.10 | `--music-gain` |
| Sound effects | -7 dB | `--sfx-db` |
| Music fade-out at the end (when not cut) | 1.2 s | style.json |
| Limiter | -1 dB, latency compensated | style.json |

## Drum detection

`--drums auto` finds the first kick drum: the 40-110 Hz band in 10 ms blocks, the first block within 8 dB of the
song's loud level. It prints the time. Check it: if the song starts with vocals over a quiet intro, the vocals are the
loud moment, so give `--drums <song seconds>` where the vocals start. If the song starts with drums (no intro, the
detected time < 1 s), the whole song plays at the normal level. `--drums none` = no intro step.

## Sound effects

`--sfx FILE@SEC`: SEC is the word's start from `data/words.json`. The script finds the effect's own hit (first sample
at 10% of its peak) and the word's real onset in the audio (the rise after the gap before the word, within
-0.15/+0.25 s), and lines them up. `--cut-music-at-sfx` stops the music on the first effect's hit (30 ms fade).

The creator supplies the sound files. Popular meme sounds (vine boom, bruh...) are easy to find, but their licences
vary: use ones they have the right to post.

## Music

Use a file the creator provides. Songs from major labels baked into an upload can be muted or limit reach on
Instagram/TikTok; the safe route for those is adding the song in the app, with this mix as the voice + SFX track.

## Verify (the script does this)

- sync vs the source = 0 samples (anything else: don't deliver)
- speech gain ≈ +6 dB at 200%
- loudness around -11 LUFS, true peak ≤ -1 dB
