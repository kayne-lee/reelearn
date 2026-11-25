"""Shared look-and-feel for every reelearn episode.

Style: deep indigo gradient with soft color glows, vivid accents.
Word-synced captions in the upper third, the main visual in the middle,
the bottom ~20% left empty for platform UI.

Frame is 9 x 16 units (1080x1920). y runs from -8 (bottom) to +8 (top).
Everything centers on x = 0; the safe area is symmetric.
"""
from pathlib import Path

import numpy as np
from manim import VGroup, Text, RoundedRectangle, config as _config, ManimColor, interpolate_color

# Lock the 9:16 frame regardless of CLI quality flags.
_config.frame_width = 9
_config.frame_height = 16

# ---------------------------------------------------------------- colors
BG_TOP = "#0B1033"     # gradient top (deep indigo)
BG_BOTTOM = "#170A2B"  # gradient bottom (plum)
GLOWS = [              # (x frac, y frac, radius frac, color, strength) soft light pools
    (0.15, 0.22, 0.55, "#2DD4BF", 0.22),
    (0.90, 0.62, 0.60, "#C026D3", 0.20),
    (0.40, 0.95, 0.45, "#6366F1", 0.18),
]

FG = "#FFFFFF"
MUTED = "#C9CCE0"      # non-emphasized caption words (light, not gray-on-black)
FAINT = "#4B4F7A"      # hairlines, axes, outlines
EMPH = "#FFD166"       # emphasized caption words (bold + this color)
PALETTE = ["#FF5D73", "#2EE6C5", "#A78BFA", "#FFB547", "#5AB2FF"]

FONT = "Avenir Next"

# ---------------------------------------------------------------- layout (scene units)
SAFE_TOP = 7.2
SAFE_BOTTOM = -4.6
SAFE_LEFT = -3.4
SAFE_RIGHT = 3.4
SAFE_CENTER_X = 0.0

CAPTION_Y = 4.7        # center of the caption block (upper third)
VISUAL_Y = -0.6        # center of the main 2D visual (3D visuals sit at screen center)
LABEL_Y = -4.2         # small status badge under the visual

# Captions
CAPTION_SIZE = 56
CAPTION_LINE_CHARS = 16   # max characters per caption line
CAPTION_MAX_LINES = 2


def T(s, size=48, color=FG, weight="BOLD", **kw):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def badge(s, color=FG, size=30, stroke=FAINT):
    """Outlined rounded badge with a faint tint of its stroke color."""
    label = T(s, size=size, color=color, weight="MEDIUM")
    box = RoundedRectangle(
        corner_radius=0.3,
        width=label.width + 0.6,
        height=label.height + 0.36,
        stroke_color=stroke, stroke_width=2.5,
        fill_color=interpolate_color(ManimColor(BG_TOP), ManimColor(stroke), 0.18), fill_opacity=0.9,
    )
    return VGroup(box, label.move_to(box))


def background_image(width: int, height: int) -> str:
    """Render (once, cached) the gradient + glow background PNG at exactly this size."""
    out = Path(_config.media_dir) / "backgrounds" / f"bg_{width}x{height}.png"
    if out.exists():
        return str(out)
    from PIL import Image

    def rgb(h):
        return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)

    y = np.linspace(0, 1, height)[:, None, None]
    img = rgb(BG_TOP) * (1 - y) + rgb(BG_BOTTOM) * y
    img = np.broadcast_to(img, (height, width, 3)).copy()
    yy, xx = np.mgrid[0:height, 0:width]
    for fx, fy, fr, color, strength in GLOWS:
        d = np.hypot(xx - fx * width, yy - fy * height) / (fr * width)
        w = (np.exp(-d ** 2 * 2.5) * strength)[..., None]
        img = img * (1 - w) + rgb(color) * w
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA").save(out)
    return str(out)
