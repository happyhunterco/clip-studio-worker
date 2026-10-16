"""Word-level transcript of the clip (Whisper large-v3-turbo).

Usage: python transcribe.py <project> [--prompt "Names, Brands, Jargon"] [--language en]
Apple Silicon uses mlx-whisper; everything else uses faster-whisper.
Writes data/words.json ([{w, s, e, p}]) and prints the transcript with times. Words Whisper was unsure of (p < 0.5)
are listed at the end: check them against the audio.
"""
import argparse
import json
import os
import platform

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--prompt", default="")
ap.add_argument("--language", default="en")
args = ap.parse_args()
proj = os.path.abspath(args.project)
audio = os.path.join(proj, "src", "audio16k.wav")
words, segs = [], []

if platform.system() == "Darwin" and platform.machine() == "arm64":
    import mlx_whisper
    res = mlx_whisper.transcribe(audio, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True,
                                 language=args.language, condition_on_previous_text=False, initial_prompt=args.prompt or None)
    for seg in res["segments"]:
        segs.append((seg["start"], seg["end"], seg["text"].strip()))
        for w in seg.get("words", []):
            words.append({"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3), "p": round(w.get("probability", 0), 3)})
else:
    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3-turbo", device="auto", compute_type="auto")
    it, _ = model.transcribe(audio, word_timestamps=True, language=args.language, condition_on_previous_text=False,
                             initial_prompt=args.prompt or None, vad_filter=False)
    for seg in it:
        segs.append((seg.start, seg.end, seg.text.strip()))
        for w in seg.words or []:
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})

words = [w for w in words if w["w"]]
json.dump(words, open(os.path.join(proj, "data", "words.json"), "w"), indent=0)
for s, e, t in segs:
    print(f"[{s:6.2f}-{e:6.2f}] {t}")
unsure = [w for w in words if w["p"] < 0.5]
print(f"\n{len(words)} words -> data/words.json")
if unsure:
    print("Low-confidence words (check these):", ", ".join(f"{w['w']}@{w['s']:.2f}" for w in unsure))
