"""EpisodeScene: the base class every episode inherits from.

    with self.narrate("Every point joins the *closest* centroid.") as t:
        self.play(..., run_time=t.get_remaining_duration())

- The text is spoken AND shown as word-synced captions (one source of truth).
- *asterisks* mark emphasized words (bold white + blue selection box).
- Animations inside the block run while the line is spoken; the block
  ends when the line finishes.

    self.set_label("Round 2 · Assign")   # small outlined status badge under the visual
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from manim import FadeIn, FadeOut
from manim_voiceover import VoiceoverScene

from .captions import CaptionTrack, assign_times, chunk_words, load_alignment, parse_words, strip_marks
from .style import SAFE_CENTER_X, LABEL_Y, badge
from .voice import get_voice


class EpisodeScene(VoiceoverScene):
    def setup(self):
        super().setup()
        self.set_speech_service(get_voice())
        self._captions = None
        self._label = None

    # ------------------------------------------------------------ narration
    @contextmanager
    def narrate(self, text: str):
        words = parse_words(text)
        with self.voiceover(text=strip_marks(text)) as tracker:
            audio = Path(tracker.cache_dir) / tracker.data["original_audio"]
            assign_times(words, tracker.duration, load_alignment(audio), len(strip_marks(text)))
            if self._captions is not None:
                self._captions.clear_updaters()
                self.remove(self._captions)
            self._captions = CaptionTrack(chunk_words(words))
            self.add(self._captions)
            yield tracker
        self._captions.clear_updaters()

    def clear_captions(self):
        if self._captions is not None:
            self._captions.clear_updaters()
            self.remove(self._captions)
            self._captions = None

    # ------------------------------------------------------------ status badge
    def label_anims(self, text: str | None, **kw):
        """Animations that swap the status badge (None removes it). Use inside self.play."""
        anims = []
        if self._label is not None:
            anims.append(FadeOut(self._label))
        self._label = None
        if text:
            self._label = badge(text, **kw).move_to([SAFE_CENTER_X, LABEL_Y, 0])
            anims.append(FadeIn(self._label))
        return anims

    def set_label(self, text: str | None, run_time: float = 0.3, **kw):
        self.play(*self.label_anims(text, **kw), run_time=run_time)
