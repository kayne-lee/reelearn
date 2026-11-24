"""Shared look-and-feel for every reelearn episode.

Frame is 9 x 16 units (1080x1920). y runs from -8 (bottom) to +8 (top).
Keep important content inside SAFE: platforms cover the bottom ~20%
(captions, username) and the right edge (like/comment buttons).
"""
from manim import (
    VGroup, Text, RoundedRectangle, FadeIn, FadeOut, UP, DOWN, LEFT, RIGHT, ORIGIN,
)

BG = "#0E1117"
FG = "#E6EDF3"
MUTED = "#7D8590"
ACCENT = "#FFD166"
PALETTE = ["#FF6B6B", "#4ECDC4", "#A78BFA", "#F4A261", "#60A5FA"]

FONT = "Avenir Next"

# Safe area (scene units)
SAFE_TOP = 7.2
SAFE_BOTTOM = -4.6
SAFE_LEFT = -4.0
SAFE_RIGHT = 3.4
SAFE_CENTER_X = (SAFE_LEFT + SAFE_RIGHT) / 2

CAPTION_Y = -3.6
TITLE_Y = 6.3


def T(s, size=48, color=FG, weight="BOLD", **kw):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def caption(s, size=46, color=FG):
    """Big centered on-screen caption, wrapped manually with \\n."""
    lines = VGroup(*[T(line, size=size, color=color) for line in s.split("\n")])
    lines.arrange(DOWN, buff=0.18)
    max_w = SAFE_RIGHT - SAFE_LEFT
    if lines.width > max_w:
        lines.scale_to_fit_width(max_w)
    lines.move_to([SAFE_CENTER_X, CAPTION_Y, 0])
    return lines


def pill(s, color=ACCENT, size=34):
    label = T(s, size=size, color=BG)
    box = RoundedRectangle(
        corner_radius=0.28,
        width=label.width + 0.7,
        height=label.height + 0.4,
        fill_color=color, fill_opacity=1, stroke_width=0,
    )
    return VGroup(box, label.move_to(box))

# Lock the 9:16 frame regardless of CLI quality flags.
from manim import config as _config
_config.frame_width = 9
_config.frame_height = 16
