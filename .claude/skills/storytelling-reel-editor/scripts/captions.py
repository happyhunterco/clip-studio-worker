"""Turn data/words.json into 2-3 word caption chunks and write page/data.js (STYLE, WORDS, CAPS, NFRAMES).

Usage: python captions.py <project>
Optional <project>/captions.json (all keys optional):
{
  "replace":        {"a.m.": "am", "gonna": "going to"},          # one word -> one word (match ignores case/punctuation)
  "phrase_replace": [["with toss", "to toss"], ["editor two", "Editor 2"]],   # same number of words on both sides
  "overrides":      [["I should", "wake up with", "seven fully", "edited reels"]],  # hand-set chunking for a phrase
  "breaks_before":  ["Last"],                                      # force a new chunk before these words
  "remove":         [["hole", 41.0]],                              # drop a word Whisper invented: [word, at/after seconds]
  "hide":           [[38.9, 40.1]]                                 # no captions in these time ranges (e.g. a blooper insert)
}
Overrides are anchored on the words themselves (not times), so they survive re-cuts.
"""
import json
import os
import re
import sys

proj = os.path.abspath(sys.argv[1])
style = json.load(open(os.path.join(proj, "style.json")))
C = style["captions"]
meta = json.load(open(os.path.join(proj, "project.json")))
words = json.load(open(os.path.join(proj, "data", "words.json")))
cfgp = os.path.join(proj, "captions.json")
cfg = json.load(open(cfgp)) if os.path.exists(cfgp) else {}
END = meta["nframes"] / style["fps"]
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
WEAK = set("a an the to of my your in for and i i've i'm that this from with like so but can at on how as our is it's "
           "you'll you're we we're they their his her its be was are while when if because or about into than just very really".split())

# ---- word fixes
for wd, after in cfg.get("remove", []):
    i = next((i for i, x in enumerate(words) if norm(x["w"]) == norm(wd) and x["s"] >= after - 0.05), None)
    if i is None:
        print(f"WARNING remove: '{wd}' not found after {after}s")
    else:
        if i and not re.search(r"[,.?!]$", words[i - 1]["w"]) and re.search(r"[,.?!]$", words[i]["w"]):
            words[i - 1]["w"] += re.search(r"[,.?!]+$", words[i]["w"]).group(0)
        words.pop(i)
rep = {norm(k): v for k, v in cfg.get("replace", {}).items()}
for x in words:
    k = norm(x["w"])
    if k in rep:
        trail = re.search(r"[,.?!]*$", x["w"]).group(0)
        x["w"] = rep[k] + trail
for a, b in cfg.get("phrase_replace", []):
    A, B = [norm(t) for t in a.split()], b.split()
    for i in range(len(words) - len(A) + 1):
        if [norm(w["w"]) for w in words[i:i + len(A)]] == A:
            for k, t in enumerate(B[:len(A)]):
                trail = re.search(r"[,.?!]*$", words[i + k]["w"]).group(0)
                words[i + k]["w"] = t + trail

# ---- merge Whisper sub-tokens ("2" ",000" -> "2,000"; "$2" ".8" -> "$2.8")
merged = []
for w in words:
    if merged and re.match(r"^[,.]\d|^%$|^'s$", w["w"]):
        merged[-1] = {**merged[-1], "w": merged[-1]["w"] + w["w"], "e": w["e"]}
    else:
        merged.append(dict(w))
words = merged

starts = {i for i, x in enumerate(words) if i and words[i - 1]["w"][-1:] in ".?!"}
starts |= {i for i, x in enumerate(words) if norm(x["w"]) in {norm(b) for b in cfg.get("breaks_before", [])}}
toks = []
for i, w in enumerate(words):
    brk = bool(re.search(r"[,.?!]$", w["w"]))
    t = re.sub(r"[,.?!]+$", "", w["w"])
    toks.append({"t": t, "s": w["s"], "e": w["e"], "brk": brk})
for i in starts:
    toks[i - 1]["brk"] = True


def cost(ch, nxt):
    text = " ".join(x["t"] for x in ch)
    c = 0.0
    if len(text) > C["max_chars"]:
        c += (len(text) - C["max_chars"]) * 0.6
    if norm(ch[-1]["t"]) in WEAK and nxt is not None:
        c += 3.0
    if re.match(r"^\$?\d", ch[-1]["t"]) and nxt is not None:
        c += 2.0        # keep a number with its noun ("10,000 followers")
    if len(ch) == 1:
        c += 0.8
    return c


runs, cur = [], []
for i, tk in enumerate(toks):
    cur.append(tk)
    nxt = toks[i + 1] if i + 1 < len(toks) else None
    if nxt is None or tk["brk"] or nxt["s"] - tk["e"] > C["gap_break_s"]:
        runs.append(cur)
        cur = []
chunks = []
for run in runs:
    n = len(run)
    best, back = [0.0] + [1e18] * n, [0] * (n + 1)
    for j in range(1, n + 1):
        for k in range(1, C["max_words"] + 1):
            if j - k < 0:
                break
            v = best[j - k] + cost(run[j - k:j], run[j] if j < n else None) + 1
            if v < best[j]:
                best[j], back[j] = v, j - k
    seg, j = [], n
    while j > 0:
        seg.append(run[back[j]:j])
        j = back[j]
    chunks += seg[::-1]

caps = []
for i, c in enumerate(chunks):
    nxt_s = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else c[-1]["e"] + 0.6
    e = min(nxt_s, c[-1]["e"] + C["hold_s"], END)
    caps.append({"s": round(max(0.0, c[0]["s"] - C["lead_s"]), 3), "e": round(e - C["lead_s"], 3), "t": " ".join(x["t"] for x in c)})

# ---- hand-set phrases
for texts in cfg.get("overrides", []):
    seq = [norm(t) for t in " ".join(texts).split()]
    j0 = next((j for j in range(len(toks)) if [norm(x["t"]) for x in toks[j:j + len(seq)]] == seq), None)
    if j0 is None:
        print(f"WARNING override not found: {' | '.join(texts)}")
        continue
    span = toks[j0:j0 + len(seq)]
    out, i = [], 0
    for tx in texts:
        out.append({"s": round(span[i]["s"] - C["lead_s"], 3), "e": 0, "t": " ".join(x["t"] for x in span[i:i + len(tx.split())])})
        i += len(tx.split())
    nxt = toks[j0 + len(seq)]["s"] - C["lead_s"] if j0 + len(seq) < len(toks) else END
    out[-1]["e"] = round(min(span[-1]["e"] + 0.3, nxt), 3)
    t0, t1 = span[0]["s"] - C["lead_s"] - 0.01, span[-1]["s"] + 0.01
    caps = [c for c in caps if c.get("_ov") or not (t0 <= c["s"] <= t1)] + [dict(o, _ov=True) for o in out]
    caps.sort(key=lambda c: c["s"])
    for k, c in enumerate(caps):
        if c["e"] == 0:
            c["e"] = caps[k + 1]["s"] if k + 1 < len(caps) else END

cen = {norm(k): v for k, v in C.get("censor", {}).items()}
for c in caps:
    c.pop("_ov", None)
    c["t"] = " ".join(cen.get(norm(t), t) for t in c["t"].split())
for x, y in zip(caps, caps[1:]):
    x["e"] = min(x["e"], y["s"])
for h0, h1 in cfg.get("hide", []):
    caps = [c for c in caps if c["e"] <= h0 or c["s"] >= h1]

open(os.path.join(proj, "page", "data.js"), "w").write(
    f"window.STYLE={json.dumps(style)};window.NFRAMES={meta['nframes']};"
    f"window.WORDS={json.dumps([{'w': w['w'], 's': w['s'], 'e': w['e']} for w in words])};window.CAPS={json.dumps(caps)};")
json.dump(caps, open(os.path.join(proj, "data", "captions.json"), "w"), indent=0)
print(f"{len(caps)} captions -> page/data.js")
for c in caps:
    print(f"{c['s']:6.2f}-{c['e']:6.2f}  {c['t']}")
