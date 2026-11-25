"""Word-synced captions.

The narration text is the caption text. Mark emphasized words with *asterisks*:

    "Every point joins the *closest* centroid."

Emphasized words render bold white with a blue selection box; the rest are gray.
Words appear exactly when they are spoken, in short chunks (≤ 2 lines).
"""
from __future__ import annotations

import json
import re
import html
from dataclasses import dataclass
from pathlib import Path

from manim import VGroup, Rectangle, Dot, MarkupText, DOWN

from .style import (
    FONT, FG, MUTED, SELECT, CAPTION_Y, CAPTION_SIZE, CAPTION_LINE_CHARS, CAPTION_MAX_LINES, SAFE_CENTER_X,
)


def strip_marks(text: str) -> str:
    """Text as it should be spoken (no emphasis markers)."""
    return text.replace("*", "")


@dataclass
class Word:
    text: str          # without markers
    emph: bool
    char_start: int    # offset into strip_marks(text)
    start: float = 0.0 # seconds into the audio


def parse_words(marked: str) -> list[Word]:
    words, in_emph, clean_pos = [], False, 0
    clean = strip_marks(marked)
    for tok in marked.split():
        plain = tok.replace("*", "")
        emph = in_emph or tok.startswith("*")
        if tok.count("*") % 2 == 1:
            in_emph = not in_emph
        idx = clean.index(plain, clean_pos)
        words.append(Word(plain, emph, idx))
        clean_pos = idx + len(plain)
    return words


def assign_times(words: list[Word], duration: float, alignment: dict | None, n_chars: int):
    """Set each word's start time from ElevenLabs alignment, else proportionally."""
    if alignment:
        starts = alignment["character_start_times_seconds"]
        for w in words:
            w.start = starts[min(w.char_start, len(starts) - 1)]
    else:
        for w in words:
            w.start = duration * w.char_start / max(1, n_chars)


def chunk_words(words: list[Word]) -> list[list[Word]]:
    """Group words into caption chunks: ≤ 2 lines, break after sentence ends."""
    chunks, cur = [], []
    for w in words:
        if cur and len(_lines(cur + [w])) > CAPTION_MAX_LINES:
            # don't split an emphasized phrase: carry its start into the next chunk
            carry = []
            if w.emph:
                while cur and cur[-1].emph and len(carry) < 3:
                    carry.insert(0, cur.pop())
            if cur:
                chunks.append(cur)
            cur = carry
        cur.append(w)
        if re.search(r"[.?!:]$", w.text):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def _lines(words: list[Word]) -> list[list[Word]]:
    lines, cur, n = [], [], 0
    for w in words:
        add = len(w.text) + (1 if cur else 0)
        if cur and n + add > CAPTION_LINE_CHARS:
            lines.append(cur)
            cur, n = [], 0
            add = len(w.text)
        cur.append(w)
        n += add
    if cur:
        lines.append(cur)
    return lines


def selection_box(m):
    """Figma-style selection: thin blue rectangle with corner handles."""
    rect = Rectangle(width=m.width + 0.24, height=m.height + 0.2,
                     stroke_color=SELECT, stroke_width=3).move_to(m)
    handles = VGroup(*[
        Dot(c, radius=0.055, color=SELECT).set_stroke(FG, width=1.5)
        for c in (rect.get_corner([-1, 1, 0]), rect.get_corner([1, -1, 0]))
    ])
    return VGroup(rect, handles)


def _span(w: Word) -> str:
    color, weight = (FG, "bold") if w.emph else (MUTED, "medium")
    return f'<span foreground="{color}" font_weight="{weight}">{html.escape(w.text, quote=False)}</span>'


def build_chunk(words: list[Word]):
    """Returns [(start_time, mobject, is_box)] for one chunk, laid out and centered.

    Each line is one MarkupText (shared baseline + kerning), then sliced into
    per-word glyph groups so words can appear individually.
    """
    lines = VGroup()
    per_line = []
    for line in _lines(words):
        mt = MarkupText(" ".join(_span(w) for w in line), font=FONT, font_size=CAPTION_SIZE)
        glyphs, i, groups = mt.submobjects, 0, []
        for w in line:
            n = len(re.sub(r"\s", "", w.text))
            groups.append((w, VGroup(*glyphs[i:i + n])))
            i += n
        lines.add(mt)
        per_line.append(groups)
    lines.arrange(DOWN, buff=0.22).move_to([SAFE_CENTER_X, CAPTION_Y, 0])
    out = []
    for groups in per_line:
        for w, g in groups:
            out.append((w.start, g, False))
            if w.emph:
                out.append((w.start, selection_box(g), True))
    return out


def _set_alpha(m, a):
    """Scale every part's fill/stroke opacity by a (0..1), remembering originals."""
    for v in m.family_members_with_points():
        if not hasattr(v, "_orig_op"):
            v._orig_op = (v.get_fill_opacity(), v.get_stroke_opacity())
        f, s = v._orig_op
        v.set_fill(opacity=f * a, family=False)
        v.set_stroke(opacity=s * a, family=False)


UPCOMING_ALPHA = 0.22


class CaptionTrack(VGroup):
    """All caption words for one narration line, added once.

    A dt updater sets each word's opacity: the current chunk is shown whole
    (so lines stay centered), unspoken words faint, spoken words full. (Membership never changes: Manim's
    renderer doesn't handle mobjects whose children change mid-animation.)
    """

    def __init__(self, chunks: list[list[Word]]):
        super().__init__()
        self.elapsed = 0.0
        self.items = []  # (chunk_index, word_start, mobject, is_box)
        for ci, c in enumerate(chunks):
            for start, m, is_box in build_chunk(c):
                self.items.append((ci, start, m, is_box))
                self.add(m)
        self.chunk_starts = [c[0].start for c in chunks]
        self.add_updater(lambda m, dt: m._tick(dt))
        self._tick(0)

    def _tick(self, dt):
        self.elapsed += dt
        t = self.elapsed + 1e-3
        current = max([i for i, s in enumerate(self.chunk_starts) if s <= t], default=-1)
        for ci, start, m, is_box in self.items:
            if ci != current:
                a = 0.0
            elif start <= t:
                a = 1.0
            else:
                a = 0.0 if is_box else UPCOMING_ALPHA  # whole chunk visible (stays centered); unspoken words faint
            _set_alpha(m, a)


def load_alignment(audio_path: Path) -> dict | None:
    p = audio_path.with_suffix(".align.json")
    return json.loads(p.read_text()) if p.exists() else None
