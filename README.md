# reelearn 🎬

Narrated, code-animated short-form learning videos (Reels / TikTok / Shorts), built with
[Manim](https://www.manim.community/) and [ElevenLabs](https://elevenlabs.io) voices.
Every episode is one Python file. Every video gets the same look: a deep gradient background, 3D visuals with a slow
camera orbit, vertical 9:16, and captions synced word by word to the narration.

## One-time setup

### 1. Python environment
```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

### 2. ElevenLabs API key
1. Sign up at [elevenlabs.io](https://elevenlabs.io). The free tier (~10k characters/month) covers several
   videos. One ~45 s episode uses about 700 characters. Note that the free tier requires attribution and doesn't
   allow commercial use. If you monetize, use a paid plan (Starter or higher).
2. Go to [elevenlabs.io/app/developers/api-keys](https://elevenlabs.io/app/developers/api-keys) (sidebar: **Developers** → **API Keys**) → **Create API Key**.
   - Name it `reelearn`.
   - Permissions: enable **Text to Speech** (that's all this repo needs).
   - Optional: set a monthly character limit as a safety cap.
3. Copy the key (it starts with `sk_`; it's only shown once) and put it in `.env`:
   ```bash
   cp .env.example .env
   open -e .env   # paste it after ELEVENLABS_API_KEY=
   ```
   `.env` is git-ignored, so it never reaches GitHub.

### 3. Pick the narrator (optional)
The default is **Brian**, a deep, steady American voice that works well for instruction. To change it, set
`ELEVENLABS_VOICE_ID` in `.env`. Talking pace is ElevenLabs' `speed` setting in `reelearn/voice.py` (1.12, a bit
quicker than normal); changing it re-voices every line. Some other good options:

| Voice | ID | Character |
|---|---|---|
| Brian (default) | `nPczCjzI2devNBz1zQrb` | American, deep, calm narrator |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | British, authoritative, news-style |
| Adam | `pNInz6obpgDQGcFmaJgB` | American, deep |
| George | `JBFqnCBsd6RMkjVDRZzb` | British, warm |

You can browse more in ElevenLabs → **Voices** → **Voice Library**. Each voice's ID is in its "…" menu → *Copy voice ID*.
Delivery is tuned in `VOICE_SETTINGS` in `reelearn/voice.py`.

## Making a video
```bash
./make.sh kmeans silent    # no audio, no API credits, 720p: check the visuals
./make.sh kmeans draft     # free robotic voice, low-res: check timing and layout
./make.sh kmeans preview   # real voice, low-res
./make.sh kmeans           # real voice, 1080x1920 → out/kmeans.mp4 (upload this)
```
Voice lines are cached in `media/voiceovers/`. Re-rendering only calls ElevenLabs for lines whose text changed.

## Writing narration
```python
with self.narrate("Every point joins the *closest* centroid.") as t:
    self.play(..., run_time=t.get_remaining_duration())
```
What's spoken is exactly what's captioned. `*asterisks*` mark emphasized words. They show bold in the accent color
and aren't spoken differently.

## Layout
```
episodes/<name>.py    one episode = one EpisodeScene subclass (script + visuals)
reelearn/scene.py     EpisodeScene base (3D-capable): narrate(), set_label(), overlay()
reelearn/captions.py  word-synced captions (*emphasis* → bold + accent color)
reelearn/style.py     colors, gradient background, font, layout constants, badge()
reelearn/voice.py     ElevenLabs TTS with per-character timestamps (+ free gTTS draft)
make.sh               render entry point (draft | preview | final)
out/                  finished MP4s (git-ignored)
media/                Manim build output + voice cache (git-ignored)
```

## Episodes
| Episode | Topic | Status |
|---|---|---|
| `kmeans` | K-means clustering (3D) | ✅ done |
| `house_robber` | House Robber (LeetCode 198), explained without code | ✅ done |
| `e_means` | e-means, Meta's faster K-means (Faiss 1.16) | ✅ done |
