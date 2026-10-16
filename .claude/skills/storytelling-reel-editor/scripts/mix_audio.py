"""Build the final audio: the clip's own audio turned up, faint background music that drops when the drums kick in,
sound effects that hit exactly on a word, and the music cut on a sound effect. Then verify it.

Usage: python mix_audio.py <project> [options]
  --music FILE              background song (m4a/mp3/wav)
  --music-start SEC         where in the song to start (default 0)
  --drums auto|SEC|none     when the drums/lyrics kick in, in SONG seconds (default auto-detect)
  --sfx FILE@SEC            sound effect whose hit lands on the word starting near SEC (video time; snapped to the
                            word's real onset in the audio, within -0.15/+0.25 s). Repeatable.
  --cut-music-at-sfx        the music stops on the first sound effect's hit
  --voice-gain X            overrides style.json audio.voice_gain (2.0 = 200%)
  --intro-gain X / --music-gain X / --sfx-db DB
Writes <project>/out/mix.wav. Levels come from style.json "audio".
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--music")
ap.add_argument("--music-start", type=float, default=0.0)
ap.add_argument("--drums", default="auto")
ap.add_argument("--sfx", action="append", default=[])
ap.add_argument("--cut-music-at-sfx", action="store_true")
ap.add_argument("--voice-gain", type=float)
ap.add_argument("--intro-gain", type=float)
ap.add_argument("--music-gain", type=float)
ap.add_argument("--sfx-db", type=float)
args = ap.parse_args()
P = os.path.abspath(args.project)
meta = json.load(open(os.path.join(P, "project.json")))
A = json.load(open(os.path.join(P, "style.json")))["audio"]
voice_gain = args.voice_gain or A["voice_gain"]
intro_gain = args.intro_gain if args.intro_gain is not None else A["music_intro_gain"]
music_gain = args.music_gain if args.music_gain is not None else A["music_gain"]
sfx_db = args.sfx_db if args.sfx_db is not None else A["sfx_gain_db"]
END = meta["nframes"] / meta["fps"]
SR = 48000


def pcm(path, af="", start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(start)] if start else []) + (["-t", str(dur)] if dur else []) + ["-i", path]
    cmd += ["-ac", "1"] + (["-af", af] if af else []) + ["-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)


def onset(path):
    x = np.abs(pcm(path))
    return float(np.argmax(x > 0.1 * x.max()) / SR)


def detect_drums(path, start, span):
    """First kick-drum hit: the <110 Hz band jumps to near its loud level (10 ms blocks)."""
    k = pcm(path, "lowpass=f=110,lowpass=f=110", start, span)
    blk = 480
    lv = np.array([db(k[i:i + blk]) for i in range(0, len(k) - blk, blk)])
    loud = np.percentile(lv, 95)
    hits = np.where(lv > loud - 8)[0]
    return (hits[0] * blk / SR) if len(hits) else None


def snap_to_word(path, t):
    """Whisper word times can be ~0.1 s off. Snap to the real start of the word: the rise after the quiet dip
    between words, searched in [t-0.15, t+0.25]. Keeps t when there is no clear dip (connected speech)."""
    x = pcm(path, "highpass=f=120", max(0, t - 0.15), 0.4)
    blk = 480
    lv = np.array([db(x[i:i + blk]) for i in range(0, len(x) - blk, blk)])
    if len(lv) < 5:
        return t
    k = int(np.argmin(lv[:30]))
    rise = np.where(lv[k:] > lv[k] + 12)[0]
    if lv.max() - lv[k] < 15 or not len(rise):
        return t
    return round(max(0, t - 0.15) + (k + rise[0]) * blk / SR, 3)


src = meta["link"]
if not meta.get("has_audio", True):
    sys.exit("The clip has no audio track to mix.")
inputs, chains, mix_in = ["-i", src], [f"[0:a]aresample={SR}[v0]"], ["[v0]"]
report = []
sfx_hits = []
for k, s in enumerate(args.sfx):
    f, at = s.rsplit("@", 1)
    raw_at = float(at)
    at = snap_to_word(src, raw_at)
    o = onset(f)
    delay = max(0, int(round((at - o) * 1000)))
    inputs += ["-i", f]
    chains.append(f"[{len(inputs) // 2 - 1}:a]aresample={SR},volume={sfx_db}dB,adelay={delay}|{delay}[s{k}]")
    mix_in.append(f"[s{k}]")
    sfx_hits.append(at)
    report.append(f"sfx {os.path.basename(f)}: hit at {o:.3f}s into the file -> lands at {at:.3f}s "
                  f"(asked {raw_at:.3f}s, snapped to the word's onset) ({sfx_db:+.1f} dB)")
chains.append(f"{''.join(mix_in)}amix=inputs={len(mix_in)}:normalize=0:duration=first,volume={voice_gain}[vo]")
final = "[vo]"

if args.music:
    span = END + 1
    if args.drums == "none":
        dr = None
    elif args.drums == "auto":
        dr = detect_drums(args.music, args.music_start, min(span, 90))
    else:
        dr = float(args.drums) - args.music_start
    if dr is not None and dr < 1.0:
        dr = None       # no quiet intro: whole song at the normal level
    cut = min(sfx_hits) if (args.cut_music_at_sfx and sfx_hits) else None
    parts = []
    if dr is not None:
        parts.append(f"if(lt(t,{dr - 0.03:.3f}),{intro_gain},if(lt(t,{dr:.3f}),{intro_gain}-{intro_gain - music_gain}*(t-{dr - 0.03:.3f})/0.03,")
    tail = f"{music_gain}"
    if cut is not None:
        tail = f"if(lt(t,{cut - 0.03:.3f}),{music_gain},if(lt(t,{cut:.3f}),{music_gain}-{music_gain}*(t-{cut - 0.03:.3f})/0.03,0))"
    expr = "".join(parts) + tail + ("))" if dr is not None else "")
    fade = "" if cut is not None else f",afade=t=out:st={max(0, END - A['music_fade_out_s']):.3f}:d={A['music_fade_out_s']}"
    inputs += ["-ss", str(args.music_start), "-i", args.music]
    mi = len([x for x in inputs if x == "-i"]) - 1
    chains.append(f"[{mi}:a]aresample={SR},atrim=0:{END:.3f},asetpts=N/SR/TB,afade=t=in:d=0.03,asetnsamples=n=48,volume='{expr}':eval=frame{fade}[mu]")
    chains.append("[vo][mu]amix=inputs=2:normalize=0:duration=first[vm]")
    final = "[vm]"
    report.append(f"music {os.path.basename(args.music)} from {args.music_start:.2f}s: "
                  + (f"{intro_gain:.0%} until the drums at video {dr:.2f}s, then {music_gain:.0%}" if dr is not None else f"{music_gain:.0%} throughout")
                  + (f", cut on the sound effect at {cut:.2f}s" if cut is not None else f", {A['music_fade_out_s']}s fade-out"))
lim = 10 ** (A["limit_db"] / 20)
chains.append(f"{final}alimiter=limit={lim:.3f}:level=0:latency=1[m]")
out = os.path.join(P, "out", "mix.wav")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(chains), "-map", "[m]", "-t", f"{END:.3f}", "-c:a", "pcm_s24le", out]
subprocess.run(cmd, check=True)

# ---- verify: sync with the source, gain, loudness, peak
v, m = pcm(src), pcm(out)
seg = slice(int(min(5, END / 4) * SR), int(min(15, END * 0.6) * SR))
lags = range(-2400, 2400, 4)
lag = max(lags, key=lambda L: float(np.dot(v[seg], m[seg.start + L:seg.stop + L])) if seg.start + L >= 0 else -1e18)
eb = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = [l.split("I:")[1].strip() for l in eb.splitlines() if l.strip().startswith("I:")][-1]
peak = [l.split("Peak:")[1].strip() for l in eb.splitlines() if l.strip().startswith("Peak:")][-1]
print("\n".join(report))
print(f"voice x{voice_gain} ({voice_gain:.0%}); speech gain measured {db(m[seg]) - db(v[seg]):+.1f} dB")
print(f"loudness {lufs}, true peak {peak}, sync vs source {lag} samples (must be 0)")
print(f"-> {out}")
if lag != 0:
    sys.exit("SYNC ERROR: the mix is offset from the video")
