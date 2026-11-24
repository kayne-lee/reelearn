# reelearn 🎬

Code-generated short-form learning videos (Reels / TikTok / Shorts), built with [Manim](https://www.manim.community/).
Every episode is a Python file. Same look, vertical 9:16, safe-zone aware.

## Setup
```bash
uv venv --python 3.12 && uv pip install manim
```

## Render
```bash
./make.sh kmeans preview   # 540x960 @15fps, fast
./make.sh kmeans           # 1080x1920 @30fps, final → out/kmeans.mp4
```

## Layout
- `reelearn/style.py`: colors, fonts, safe area, `caption()` and `pill()` helpers. Shared by all episodes.
- `episodes/<name>.py`: one scene per episode.
- `manim.cfg`: background and output dirs.

Safe area: keep text above y = -4.6 and left of x = 3.4 (the platforms cover the bottom and right edges).

## Episodes
| Episode | Topic | Length |
|---|---|---|
| `kmeans` | K-means clustering | ~33 s |
