#!/bin/bash
# Rendered frames + audio -> final MP4 (H.264 High, BT.709, CRF 17, AAC 320k, 1080x1920).
#   bash encode.sh <project> <out.mp4> [audio file]   (audio default: <project>/out/mix.wav, else the clip's own audio)
set -e
P="$(cd "$1" && pwd)"; OUT="$2"; AUD="${3:-}"
FPS=$(python3 -c "import json;print(json.load(open('$P/project.json'))['fps'])")
if [ -z "$AUD" ]; then if [ -f "$P/out/mix.wav" ]; then AUD="$P/out/mix.wav"; else AUD="$P/src/$(ls "$P/src" | grep '^source\.' | head -1)"; fi; fi
ffmpeg -v error -y -framerate "$FPS" -i "$P/render/%05d.jpg" -i "$AUD" -map 0:v -map 1:a:0 \
  -vf "scale=in_color_matrix=bt601:in_range=pc:out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -tune film -aq-mode 3 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT"
echo "-> $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s, audio: $(basename "$AUD"))"
