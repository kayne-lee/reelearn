#!/usr/bin/env bash
# Usage: ./make.sh <episode> [preview|final]   e.g. ./make.sh kmeans preview
set -euo pipefail
cd "$(dirname "$0")"
ep="${1:?episode name, e.g. kmeans}"
mode="${2:-final}"
case "$mode" in
  preview) flags=(-ql -r 540,960 --frame_rate 15) ;;
  final)   flags=(-qh -r 1080,1920 --frame_rate 30) ;;
  *) echo "mode must be preview or final"; exit 1 ;;
esac
export PYTHONWARNINGS=ignore
.venv/bin/manim "${flags[@]}" --disable_caching "episodes/$ep.py" 2>&1 | grep -v '^\s*$' | tail -2
mkdir -p out
latest=$(ls -1t media/videos/"$ep"/*/*.mp4 | head -1)
suffix=""; [[ $mode == preview ]] && suffix="-preview"
cp "$latest" "out/$ep$suffix.mp4"
echo "→ out/$ep$suffix.mp4"
