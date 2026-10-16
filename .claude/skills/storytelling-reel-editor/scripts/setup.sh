#!/bin/bash
# One-time setup for the storytelling-reel-editor skill.
# Creates ~/.reel-editor/ with a Python venv (Whisper + numpy + Pillow) and puppeteer-core (drives your Chrome).
# Re-running is safe: it only installs what is missing.   Override the location with REEL_EDITOR_HOME=/path
set -e
RE_HOME="${REEL_EDITOR_HOME:-$HOME/.reel-editor}"
OS="$(uname -s)"; ARCH="$(uname -m)"
missing=0
need() { if ! command -v "$1" >/dev/null 2>&1; then echo "MISSING: $1  ->  $2"; missing=1; fi; }
if [ "$OS" = "Darwin" ]; then
  need ffmpeg  "brew install ffmpeg   (Homebrew: https://brew.sh)"
  need node    "brew install node"
else
  need ffmpeg  "sudo apt install ffmpeg   (or your distro's package manager)"
  need node    "install Node 18+ from https://nodejs.org"
fi
need ffprobe "comes with ffmpeg"
need npm     "comes with Node"

# Python: prefer versions that have wheels for the Whisper libraries
PY=""
for v in python3.12 python3.13 python3.11 python3.14 python3.10 python3; do
  if command -v "$v" >/dev/null 2>&1; then PY="$(command -v $v)"; break; fi
done
[ -z "$PY" ] && { echo "MISSING: python3  ->  brew install python@3.12  (or python.org)"; missing=1; }

# Chrome / Chromium for rendering
CHROME="${CHROME:-}"
if [ -z "$CHROME" ]; then
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "/Applications/Chromium.app/Contents/MacOS/Chromium" \
           "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary" "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
           "$(command -v google-chrome 2>/dev/null)" "$(command -v google-chrome-stable 2>/dev/null)" "$(command -v chromium 2>/dev/null)" "$(command -v chromium-browser 2>/dev/null)" "/opt/pw-browsers/chromium"; do
    if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
  done
fi
[ -z "$CHROME" ] && { echo "MISSING: Google Chrome  ->  install from https://www.google.com/chrome (or set CHROME=/path/to/chrome)"; missing=1; }

if [ "$missing" = 1 ]; then echo "Install the missing tools above, then run setup again."; exit 1; fi

mkdir -p "$RE_HOME"
if [ ! -x "$RE_HOME/venv/bin/python" ]; then
  echo "Creating Python venv with $PY ($($PY --version 2>&1))"
  "$PY" -m venv "$RE_HOME/venv"
fi
VPY="$RE_HOME/venv/bin/python"
"$VPY" -m pip install -q --upgrade pip
"$VPY" -m pip install -q numpy pillow
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
  "$VPY" -c "import mlx_whisper" 2>/dev/null || { echo "Installing mlx-whisper (Apple Silicon)..."; "$VPY" -m pip install -q mlx-whisper; }
else
  "$VPY" -c "import faster_whisper" 2>/dev/null || { echo "Installing faster-whisper..."; "$VPY" -m pip install -q faster-whisper; }
fi

mkdir -p "$RE_HOME/node"
if [ ! -d "$RE_HOME/node/node_modules/puppeteer-core" ]; then
  echo "Installing puppeteer-core..."
  (cd "$RE_HOME/node" && { [ -f package.json ] || npm init -y >/dev/null; } && npm install --silent --no-audit --no-fund puppeteer-core@23.11.1)
fi

"$VPY" - "$RE_HOME/env.json" "$CHROME" <<'EOF'
import json, sys
json.dump({"chrome": sys.argv[2]}, open(sys.argv[1], "w"), indent=1)
EOF
echo "READY  (home: $RE_HOME, python: $("$VPY" --version 2>&1), chrome: $CHROME)"
echo "Note: the first transcription downloads the Whisper model (~1.5 GB) once."
