# reelearn: notes for Claude

The user comes back to this repo to make new short-form learning videos. **Keep it organized**:
follow the structure below exactly. Don't add one-off scripts or loose files, and don't duplicate helpers.

## Structure (do not deviate)
- `episodes/<slug>.py`: one file per episode, with one `EpisodeScene` subclass. The narration script lives
  inline as `self.narrate(...)` calls, so the script and the visuals stay in one place.
- `reelearn/`: the shared library. Anything reusable across episodes goes here, not in an episode:
  - `scene.py`: `EpisodeScene` (`narrate`, `set_tag`/`tag_anims`, `title_card`, `clear_caption`)
  - `style.py`: palette, font, safe-area constants, `caption()`, `pill()`
  - `voice.py`: ElevenLabs TTS + gTTS draft fallback
- `make.sh <slug> [draft|preview|final]` is the only render entry point. Finished file → `out/<slug>.mp4`.
- Update the **Episodes** table in `README.md` whenever an episode is added or changes status.

## Making a new episode
1. Copy the shape of `episodes/kmeans.py`: imports, data at the top, then `class X(EpisodeScene)`.
2. Script: hook in the first 2 s (`title_card` is visible from frame 0), one idea per video, 30–60 s total,
   end with a "follow for more" line.
3. Wrap each beat in `with self.narrate("spoken line", caption_text="short\ncaption") as t:` and size
   animations to `t.get_remaining_duration()` / `t.duration`. Give long spoken lines a short `caption_text`
   (≤ 3 lines, ~28 chars each), because auto-wrapped long captions get shrunk.
4. Make visuals truthful: compute them (e.g. actually run the algorithm with numpy). Never fake the math.
5. Render `./make.sh <slug> draft` (free, no API credits), extract frames, and check layout before using credits.
6. Then `./make.sh <slug>` for the final. Commit the episode file and the README update together.

## Layout rules
- Frame is 9 × 16 units (1080×1920). Keep text inside the SAFE_* bounds in `style.py`: nothing important
  below y = -4.6 or right of x = 3.4, where the platforms put their buttons and captions.
- Title at `TITLE_Y`, status pill at `TAG_Y`, captions at `CAPTION_Y`, main visual in between.

## Gotchas
- Manim's `-ql`/`-qh` flags reset resolution to landscape. `make.sh` passes `-r` explicitly; keep it that way.
- Swapping text with `Transform` garbles letters. Fade out/in instead (that's what `tag_anims` does).
- The ElevenLabs key lives in `.env` (git-ignored). Never print it or commit it.
- The voice cache is keyed on text + voice + model + settings. Changing a line re-bills only that line.
