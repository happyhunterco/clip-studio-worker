"""QA of a finished MP4: frames at the given times (with the no-go zones outlined) + format and audio facts.

Usage: python check.py <project> <video.mp4> [t1 t2 ...]     (default: 8 evenly spaced times)
Writes <project>/out/check.jpg. Look at it: overlays above the head, captions readable, nothing in the red outlines.
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

P, vid = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
st = json.load(open(os.path.join(P, "style.json")))
Z = st["safe_area"]
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", vid], capture_output=True, text=True).stdout)
dur = float(info["format"]["duration"])
ts = [float(x) for x in sys.argv[3:]] or [round(dur * (k + 0.5) / 8, 2) for k in range(8)]
W, H = 270, 480
cols = min(len(ts), 6)
sheet = Image.new("RGB", (W * cols, H * ((len(ts) + cols - 1) // cols)), (0, 0, 0))
tmp = os.path.join(P, "out", "_check.png")
for k, t in enumerate(ts):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", vid, "-frames:v", "1", tmp], check=True)
    im = Image.open(tmp).convert("RGB")
    d = ImageDraw.Draw(im)
    for box in ([0, 0, 1080, Z["top"]], [0, Z["bottom"], 1080, 1920], [Z["rail_x"], Z["rail_from_y"], 1080, Z["bottom"]]):
        d.rectangle(box, outline=(255, 40, 40), width=6)
    d.text((20, 1850), f"{t:.2f}s", fill=(255, 255, 0))
    sheet.paste(im.resize((W, H)), ((k % cols) * W, (k // cols) * H))
os.remove(tmp)
out = os.path.join(P, "out", "check.jpg")
sheet.save(out, quality=88)
v = next(s for s in info["streams"] if s["codec_type"] == "video")
a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
eb = subprocess.run(["ffmpeg", "-hide_banner", "-i", vid, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr if a else ""
lufs = [l.split("I:")[1].strip() for l in eb.splitlines() if l.strip().startswith("I:")]
peak = [l.split("Peak:")[1].strip() for l in eb.splitlines() if l.strip().startswith("Peak:")]
print(f"{v['width']}x{v['height']} {v['avg_frame_rate']} fps, {dur:.2f}s, {v.get('nb_frames', '?')} frames, {v['codec_name']} {v.get('color_space', '')}")
print(f"audio: {a['codec_name']} {a['sample_rate']} Hz, loudness {lufs[-1] if lufs else '?'}, true peak {peak[-1] if peak else '?'}" if a else "audio: NONE")
print(f"contact sheet -> {out}")
