"""Set up an edit folder for one clip: probe it, pull 1080x1920 frames + 16 kHz audio, copy the page template.

Usage: python new_project.py <clip.mov|mp4> [project_dir]
Default project_dir: <clip folder>/<clip name>-edit
Layout:  src/source.<ext> (link to the clip)  src/audio16k.wav  frames/00000.jpg...  data/  page/  render/  out/
"""
import json
import os
import shutil
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
clip = os.path.abspath(sys.argv[1])
if not os.path.exists(clip):
    sys.exit(f"Clip not found: {clip}")
name = os.path.splitext(os.path.basename(clip))[0]
proj = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(os.path.dirname(clip), f"{name}-edit")
style = json.load(open(os.path.join(SKILL, "style.json")))
FPS, OW, OH = style["fps"], style["width"], style["height"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Command failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r.stdout


info = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", clip]))
v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
if not v:
    sys.exit("No video stream in the clip.")
dur = float(info["format"]["duration"])
w, h = int(v["width"]), int(v["height"])
rot = 0
for sd in v.get("side_data_list", []):
    if "rotation" in sd:
        rot = int(float(sd["rotation"]))
rot = rot or int(v.get("tags", {}).get("rotate", 0))
if abs(rot) % 180 == 90:
    w, h = h, w
transfer = v.get("color_transfer", "")
matrix = {"bt709": "bt709", "smpte170m": "bt601", "bt470bg": "bt601", "bt2020nc": "bt2020"}.get(v.get("color_space", ""), "bt709" if h >= 720 else "bt601")
warnings = []
if not a:
    warnings.append("The clip has no audio track.")
if abs(w / h - OW / OH) > 0.02:
    warnings.append(f"The clip is {w}x{h}, not 9:16: it is scaled to cover 1080x1920 and centre-cropped. Check the framing.")

vf = f"fps={FPS},scale={OW}:{OH}:force_original_aspect_ratio=increase:flags=lanczos"
if transfer in ("arib-std-b67", "smpte2084"):  # HDR (iPhone records HLG by default)
    filters = run(["ffmpeg", "-hide_banner", "-filters"])
    if " zscale " in filters:
        vf = f"zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,{vf}"
        matrix = "bt709"
        warnings.append("HDR clip: tone-mapped to SDR. Compare colours with the original; for exact colours export SDR from your editor.")
    else:
        sys.exit("This clip is HDR (" + transfer + ") and this ffmpeg can't tone-map it (no zscale).\n"
                 "Fix: export it as SDR first (CapCut: turn HDR off on export; iPhone Photos: share > Options > 'Most Compatible'),\n"
                 "or install an ffmpeg with zimg.")
vf += f",crop={OW}:{OH},scale=in_color_matrix={matrix}:in_range=tv:out_color_matrix=bt601:out_range=pc,format=yuvj420p"

for d in ("src", "data", "page", "frames", "render", "out"):
    os.makedirs(os.path.join(proj, d), exist_ok=True)
ext = os.path.splitext(clip)[1]
link = os.path.join(proj, "src", "source" + ext)
if os.path.lexists(link):
    os.remove(link)
try:
    os.symlink(clip, link)
except OSError:
    shutil.copy2(clip, link)

# page template + fonts + the project's own copy of the style (edit it per project if needed)
for f in ("index.html", "runtime.js", "icons.js"):
    shutil.copy2(os.path.join(SKILL, "template", f), os.path.join(proj, "page", f))
if not os.path.exists(os.path.join(proj, "page", "beats.js")):
    shutil.copy2(os.path.join(SKILL, "template", "beats.js"), os.path.join(proj, "page", "beats.js"))
shutil.copytree(os.path.join(SKILL, "fonts"), os.path.join(proj, "page", "fonts"), dirs_exist_ok=True)
os.makedirs(os.path.join(proj, "page", "assets"), exist_ok=True)
if not os.path.exists(os.path.join(proj, "style.json")):
    shutil.copy2(os.path.join(SKILL, "style.json"), os.path.join(proj, "style.json"))

print(f"Extracting frames ({FPS} fps, {OW}x{OH})...")
for f in os.listdir(os.path.join(proj, "frames")):
    os.remove(os.path.join(proj, "frames", f))
run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vf", vf, "-q:v", "2", "-start_number", "0", os.path.join(proj, "frames", "%05d.jpg")])
nframes = len([f for f in os.listdir(os.path.join(proj, "frames")) if f.endswith(".jpg")])
if a:
    run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vn", "-ac", "1", "-ar", "16000", os.path.join(proj, "src", "audio16k.wav")])

meta = {"source": clip, "link": link, "duration": round(dur, 3), "nframes": nframes, "fps": FPS, "src_size": [w, h], "rotation": rot,
        "src_fps": v.get("avg_frame_rate"), "color_transfer": transfer, "has_audio": bool(a), "warnings": warnings}
json.dump(meta, open(os.path.join(proj, "project.json"), "w"), indent=1)
# placeholder data so the page loads before captions exist
st = json.load(open(os.path.join(proj, "style.json")))
open(os.path.join(proj, "page", "data.js"), "w").write(
    f"window.STYLE={json.dumps(st)};window.NFRAMES={nframes};window.WORDS=[];window.CAPS=[];")
print(json.dumps(meta, indent=1))
print(f"\nProject ready: {proj}")
