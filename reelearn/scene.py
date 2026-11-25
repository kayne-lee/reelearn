"""EpisodeScene: the base class every episode inherits from.

Gives you:
  with self.narrate("Spoken line.") as t:     # voice + matching caption
      self.play(..., run_time=t.duration)      # animations sized to the speech
  self.set_tag("1 · ASSIGN")                  # top status pill, swaps cleanly
  self.title_card("K-MEANS", "clustering, explained")
"""
from __future__ import annotations

import textwrap
from contextlib import contextmanager

from manim import FadeIn, FadeOut, UP, DOWN, Write, VGroup
from manim_voiceover import VoiceoverScene

from .style import (
    ACCENT, MUTED, SAFE_CENTER_X, TITLE_Y, TAG_Y, CAPTION_CHARS, T, caption, pill,
)
from .voice import get_voice


class EpisodeScene(VoiceoverScene):
    def setup(self):
        super().setup()
        self.set_speech_service(get_voice())
        self._caption = None
        self._tag = None
        self._title = None

    # ------------------------------------------------------------ narration
    @contextmanager
    def narrate(self, text: str, caption_text: str | None = None, fade: float = 0.3):
        """Speak `text` and show it as the on-screen caption.

        Pass `caption_text` to show a shorter caption than what is spoken.
        Captions are wrapped automatically; use \\n to force breaks.
        """
        shown = caption_text or text
        if "\n" not in shown:
            shown = textwrap.fill(shown, CAPTION_CHARS)
        with self.voiceover(text=text) as tracker:
            self._swap_caption(caption(shown), fade)
            yield tracker

    def _swap_caption(self, new, fade):
        if self._caption is None:
            self.play(FadeIn(new, shift=UP * 0.2), run_time=fade)
        else:
            self.play(FadeOut(self._caption, shift=UP * 0.2), FadeIn(new, shift=UP * 0.2), run_time=fade)
        self._caption = new

    def clear_caption(self, fade: float = 0.3):
        if self._caption is not None:
            self.play(FadeOut(self._caption), run_time=fade)
            self._caption = None

    # ------------------------------------------------------------ chrome
    def title_card(self, title: str, subtitle: str | None = None):
        """Title at the top from frame 0 (the hook needs it visible immediately)."""
        t = T(title, size=96, color=ACCENT).move_to([SAFE_CENTER_X, TITLE_Y, 0])
        group = VGroup(t)
        if subtitle:
            s = T(subtitle, size=36, color=MUTED, weight="NORMAL").next_to(t, DOWN, buff=0.2)
            group.add(s)
        self.add(group)
        self._title = group
        return group

    def tag_anims(self, label: str | None, color=ACCENT):
        """Animations that swap the status pill (None removes it). Use inside self.play."""
        anims = []
        if self._tag is not None:
            anims.append(FadeOut(self._tag, scale=0.9))
        self._tag = None
        if label:
            self._tag = pill(label, color=color).move_to([SAFE_CENTER_X, TAG_Y, 0])
            anims.append(FadeIn(self._tag, scale=1.1))
        return anims

    def set_tag(self, label: str | None, color=ACCENT, run_time: float = 0.35):
        self.play(*self.tag_anims(label, color), run_time=run_time)
