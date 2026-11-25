"""Shared look-and-feel for every reelearn episode.

Style: pure black, minimal. Word-synced captions in the upper third,
the main visual in the middle, and the bottom ~20% left empty for platform UI.

Frame is 9 x 16 units (1080x1920). y runs from -8 (bottom) to +8 (top).
Everything centers on x = 0; the safe area is symmetric.
"""
from manim import VGroup, Text, RoundedRectangle, config as _config

# Lock the 9:16 frame regardless of CLI quality flags.
_config.frame_width = 9
_config.frame_height = 16

# ---------------------------------------------------------------- colors
BG = "#000000"
FG = "#FFFFFF"
MUTED = "#8B8F98"      # non-emphasized caption words, secondary labels
FAINT = "#3A3D44"      # hairlines, outlines
SELECT = "#4C7DFF"     # selection-box blue for emphasized words
PALETTE = ["#FF6B6B", "#4ECDC4", "#A78BFA", "#F4A261", "#60A5FA"]

FONT = "Avenir Next"

# ---------------------------------------------------------------- layout (scene units)
SAFE_TOP = 7.2
SAFE_BOTTOM = -4.6
SAFE_LEFT = -3.4
SAFE_RIGHT = 3.4
SAFE_CENTER_X = 0.0

CAPTION_Y = 4.7        # center of the caption block (upper third)
VISUAL_Y = -0.6        # center of the main visual
LABEL_Y = -4.2         # small status badge under the visual

# Captions
CAPTION_SIZE = 56
CAPTION_LINE_CHARS = 16   # max characters per caption line
CAPTION_MAX_LINES = 2


def T(s, size=48, color=FG, weight="BOLD", **kw):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def badge(s, color=FG, size=30, stroke=FAINT):
    """Thin outlined rounded badge, e.g. '+56%' or 'Round 2 · Assign'."""
    label = T(s, size=size, color=color, weight="MEDIUM")
    box = RoundedRectangle(
        corner_radius=0.3,
        width=label.width + 0.6,
        height=label.height + 0.36,
        stroke_color=stroke, stroke_width=2.5, fill_color=BG, fill_opacity=1,
    )
    return VGroup(box, label.move_to(box))
