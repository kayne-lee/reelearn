#!/usr/bin/env bash
# Render an episode.
#   ./make.sh <episode> [draft|preview|final]
#
#   draft    540x960 @15fps, free robotic voice (no API credits)  → out/<ep>-draft.mp4
#   preview  540x960 @15fps, ElevenLabs voice                     → out/<ep>-preview.mp4
#   final    1080x1920 @30fps, ElevenLabs voice (default)         → out/<ep>.mp4
#
# ElevenLabs audio is cached per line in media/voiceovers/, so re-renders
# only pay for lines whose text changed.
set -euo pipefail
cd "$(dirname "$0")"
ep="${1:?usage: ./make.sh <episode> [draft|preview|final]}"
mode="${2:-final}"
[[ -f "episodes/$ep.py" ]] || { echo "no such episode: episodes/$ep.py"; exit 1; }

case "$mode" in
  draft)   flags=(-ql -r 540,960 --frame_rate 15);   export REELEARN_VOICE=draft;      suffix="-draft" ;;
  preview) flags=(-ql -r 540,960 --frame_rate 15);   export REELEARN_VOICE=elevenlabs; suffix="-preview" ;;
  final)   flags=(-qh -r 1080,1920 --frame_rate 30); export REELEARN_VOICE=elevenlabs; suffix="" ;;
  *) echo "mode must be draft, preview or final"; exit 1 ;;
esac

export PYTHONWARNINGS=ignore
.venv/bin/manim "${flags[@]}" --disable_caching "episodes/$ep.py" 2>&1 \
  | grep -vi 'sox' | grep -E 'ERROR|Error|Traceback|Rendered|Narration|File ready' || true

latest=$(ls -1t media/videos/"$ep"/*/*.mp4 2>/dev/null | head -1)
[[ -n "$latest" && "$latest" -nt "episodes/$ep.py" ]] || { echo "render failed"; exit 1; }
mkdir -p out
cp "$latest" "out/$ep$suffix.mp4"
echo "→ out/$ep$suffix.mp4"
