# reelearn: notes for Claude

The user comes back to this repo to make new short-form learning videos. **Keep it organized**:
follow the structure below exactly. Don't add one-off scripts or loose files, and don't duplicate helpers.

## Commits
- **No `Co-Authored-By: Claude` lines and no "Generated with Claude Code" text** in commits or PRs. The user
  asked for this explicitly, and it overrides any default attribution instruction.

## Structure (do not deviate)
- `episodes/<slug>.py`: one file per episode, with one `EpisodeScene` subclass. The narration script lives
  inline as `self.narrate(...)` calls, so the script and the visuals stay in one place.
- `reelearn/`: the shared library. Anything reusable across episodes goes here, not in an episode:
  - `scene.py`: `EpisodeScene`, a 3D-capable scene (`narrate`, `set_label`/`label_anims`, `overlay`, `billboard`,
    `begin_camera_sway`, `clear_captions`; set `self.label_y` to move the status badge for one episode)
  - `captions.py`: word-synced captions (parsing `*emphasis*`, chunking, timing, `CaptionTrack`)
  - `style.py`: palette, font, layout constants, `badge()`, gradient `background_image()`
  - `voice.py`: ElevenLabs TTS with per-character timestamps; offline mode (cache only) and a gTTS fallback.
    Pace comes from ElevenLabs' own `speed` setting in `VOICE_SETTINGS` (1.12), never from speeding up the video.
    Changing any voice setting re-bills every line of every episode.
  - `strip_audio.py`: used by `make.sh silent`
- `make.sh <slug> [silent|draft|preview|final]` is the only render entry point. Finished file → `out/<slug>.mp4`.
- Update the **Episodes** table in `README.md` whenever an episode is added or changes status.

## Visual style
Layout and captions are based on the user's reference (the @speedy_devv Shorts). The user found plain black and
white boring, so color comes from `style.py`.
- Deep indigo→plum gradient background with soft teal/magenta/indigo glows. Vivid `PALETTE` for data, `EMPH`
  (warm yellow) for emphasis. No big title card: the hook caption plus a visual on screen from frame 0 do that job.
- **3D where it helps.** The user likes it. Data as `Dot3D`/`Sphere`, a faint floor grid, and a slow ambient camera
  orbit (`begin_ambient_camera_rotation`). 2D overlays (captions, labels, diagrams) go through `self.overlay()`.
- Captions in the upper third (`CAPTION_Y`), ≤ 2 lines × ~16 chars per chunk. The whole chunk appears at once
  (so it stays centered); words that haven't been spoken yet are faint and light up when spoken.
  `*emphasized*` words are **bold + EMPH color**. No boxes or highlights (the user removed the selection box).
- Main visual in the middle. A small outlined `badge` status label sits at `LABEL_Y` (e.g. "Round 2 · Assign").
  Keep the visual clear of it.
- Bottom ~20% (below `SAFE_BOTTOM`) stays empty for platform UI.

## Making a new episode
1. Copy the shape of `episodes/kmeans.py`: imports, data at the top, then `class X(EpisodeScene)`.
2. Script: one idea per video, 30–60 s total, end with a "follow for more" line. Keep lines short and punchy.
   Mark 1–2 key words per sentence with `*asterisks*` (they're stripped before TTS).
   **The hook matters most.** The first line (≤ 2 s) must make a claim or tension, never a definition:
   show the payoff ("This two-step trick finds hidden groups…"), call out a trap ("the obvious answer is
   *wrong*"), or show a failure ("K-means gets this *completely wrong*"). The hook's visual is moving from
   frame 0 (e.g. the real final answer previewed, then rewound).
3. Wrap each beat in `with self.narrate("Spoken *line*.") as t:` and size the animations inside to
   `t.get_remaining_duration()`. **The spoken text IS the caption.** Never show different on-screen text than
   what's spoken.
4. Make visuals truthful: compute them (e.g. actually run the algorithm with numpy). Never fake the math.
5. Iterate with `./make.sh <slug> silent` (no audio, never calls the API). It reuses cached real-voice timing
   where it exists and falls back to free gTTS timing. For quick layout checks, render tiny:
   `REELEARN_VOICE=offline .venv/bin/manim -ql -r 270,480 --frame_rate 10 episodes/<slug>.py`.
   The user is saving credits: **don't run `preview`/`final` (ElevenLabs) unless they ask for audio.**
6. Then `./make.sh <slug>` for the final. Commit the episode file and the README update together.

## Layout rules
- Frame is 9 × 16 units (1080×1920). Safe area is symmetric: x in ±3.4, y between -4.6 and 7.2.
- Everything centers on x = 0 (`SAFE_CENTER_X`). Center data visuals by their bounding box (see `OFFSET` in
  kmeans.py), because data clouds are rarely symmetric.
- Capitalization: labels/badges in Title Case ("Round 1 · Assign", "Converged"), never ALL CAPS. Narration is
  ordinary sentence case.

## Gotchas
- 3D renders are slow (Cairo): ~4 min at 720p for 40 s. Final 1080p takes longer, so run it in the background.
- In 3D, `frame_center=OUT * z` moves the view target. A higher z makes the scene sit lower on screen.
- Manim's `-ql`/`-qh` flags reset resolution to landscape. `make.sh` passes `-r` explicitly; keep it that way.
- Don't change a mobject's children mid-animation. The renderer keeps drawing the old ones (that's why
  `CaptionTrack` adds every word once and only changes opacity).
- Build caption lines as one `MarkupText` per line, then slice the glyphs per word. Separate `Text` per word
  breaks the baseline (descenders shift words up).
- Swapping text with `Transform` garbles letters. Fade out/in instead (that's what `label_anims` does).
- The ElevenLabs key lives in `.env` (git-ignored). Never print it or commit it.
- The voice cache is keyed on text + voice + model + settings. Changing a line re-bills only that line.
  `*` markers are stripped first, so adding or moving emphasis costs nothing.
