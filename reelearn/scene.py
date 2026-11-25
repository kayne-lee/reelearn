"""EpisodeScene: the base class every episode inherits from.

    with self.narrate("Every point joins the *closest* centroid.") as t:
        self.play(..., run_time=t.get_remaining_duration())

- The text is spoken AND shown as word-synced captions (one source of truth).
- *asterisks* mark emphasized words (bold + accent color).
- Animations inside the block run while the line is spoken; the block
  ends when the line finishes.

It's a ThreeDScene, so episodes can use 3D (set_camera_orientation, Dot3D,
ambient rotation, begin_camera_sway...). Captions and labels are pinned to the screen.
For other 2D overlays in a 3D episode, call self.overlay(mob); for labels attached to
3D objects that should face the camera, call self.billboard(mob).
With the default camera, 2D episodes work exactly as usual.

    self.set_label("Round 2 · Assign")   # small outlined status badge under the visual
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import numpy as np
from manim import DEGREES, FadeIn, FadeOut, ThreeDScene
from manim_voiceover import VoiceoverScene

from .captions import CaptionTrack, assign_times, chunk_words, load_alignment, parse_words, strip_marks
from .style import SAFE_CENTER_X, LABEL_Y, badge, background_image
from .voice import get_voice


class EpisodeScene(VoiceoverScene, ThreeDScene):
    def setup(self):
        super().setup()
        cam = self.camera
        cam.background_image = background_image(cam.pixel_width, cam.pixel_height)
        cam.init_background()
        cam.reset()
        self.set_speech_service(get_voice())
        self._captions = None
        self._label = None

    def overlay(self, *mobs):
        """Pin 2D mobjects to the screen (unaffected by the 3D camera)."""
        self.add_fixed_in_frame_mobjects(*mobs)
        return mobs[0] if len(mobs) == 1 else mobs

    def billboard(self, *mobs):
        """Keep mobjects at their 3D position but always facing the camera (labels on 3D objects)."""
        self.add_fixed_orientation_mobjects(*mobs)
        return mobs[0] if len(mobs) == 1 else mobs

    def begin_camera_sway(self, amplitude: float = 6 * DEGREES, period: float = 12.0):
        """Gentle back-and-forth around the current theta. Keeps depth alive while text stays readable
        (use begin_ambient_camera_rotation for a full orbit instead)."""
        tracker = self.camera.theta_tracker
        base, clock = tracker.get_value(), [0.0]

        def sway(m, dt):
            clock[0] += dt
            m.set_value(base + amplitude * np.sin(2 * np.pi * clock[0] / period))

        tracker.add_updater(sway)
        self.add(tracker)

    # ------------------------------------------------------------ narration
    @contextmanager
    def narrate(self, text: str):
        words = parse_words(text)
        with self.voiceover(text=strip_marks(text)) as tracker:
            audio = Path(tracker.cache_dir) / tracker.data["original_audio"]
            assign_times(words, tracker.duration, load_alignment(audio), len(strip_marks(text)))
            self.clear_captions()
            self._captions = CaptionTrack(chunk_words(words))
            self.overlay(self._captions)
            yield tracker
        self._captions.clear_updaters()

    def clear_captions(self):
        if self._captions is not None:
            self._captions.clear_updaters()
            self.remove(self._captions)
            self._captions = None

    # ------------------------------------------------------------ status badge
    def label_anims(self, text: str | None, y: float | None = None, **kw):
        """Animations that swap the status badge (None removes it). Use inside self.play.
        y overrides LABEL_Y for this badge; set self.label_y once to change it for a whole episode."""
        anims = []
        if self._label is not None:
            anims.append(FadeOut(self._label))
        self._label = None
        if text:
            y = y if y is not None else getattr(self, "label_y", LABEL_Y)
            self._label = badge(text, **kw).move_to([SAFE_CENTER_X, y, 0])
            self.overlay(self._label)
            anims.append(FadeIn(self._label))
        return anims

    def set_label(self, text: str | None, run_time: float = 0.3, **kw):
        self.play(*self.label_anims(text, **kw), run_time=run_time)
