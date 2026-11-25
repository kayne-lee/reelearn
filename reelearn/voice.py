"""Narration voices.

`get_voice()` picks the speech service (REELEARN_VOICE, set by make.sh):
  - elevenlabs: real voice; needs ELEVENLABS_API_KEY in .env
  - offline:    never calls the API; reuses cached real-voice lines, gTTS timing for new ones
  - draft:      gTTS only (free, robotic)

Audio is cached under media/voiceovers/, keyed by text + voice + model,
so re-rendering an unchanged line never calls the API again. ElevenLabs lines
also save <audio>.align.json (per-character timings) for synced captions.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from manim import logger
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService
from manim_voiceover.services.gtts import GTTSService

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Default narrator: "Brian", an ElevenLabs premade voice (deep, steady, American).
# Swap by setting ELEVENLABS_VOICE_ID in .env. Other good instructional males:
#   Daniel  onwK4e9ZLuTAKqWW03F9  (British, authoritative)
#   Adam    pNInz6obpgDQGcFmaJgB  (American, deep)
#   George  JBFqnCBsd6RMkjVDRZzb  (British, warm)
DEFAULT_VOICE_ID = "nPczCjzI2devNBz1zQrb"
DEFAULT_MODEL = "eleven_multilingual_v2"

# Lower stability = more expressive; higher = more consistent/neutral.
# speed: ElevenLabs' own delivery pace (0.7-1.2). The voice really talks faster; the video isn't sped up.
# Changing any setting here re-voices (and re-bills) every line.
VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 0.15,
    "use_speaker_boost": True,
    "speed": 1.12,
}


class ElevenLabsTTS(SpeechService):
    """Minimal ElevenLabs service using the current REST API."""

    def __init__(self, api_key: str, voice_id: str, model: str = DEFAULT_MODEL,
                 offline: bool = False, **kwargs):
        """offline=True never calls the API: cached lines are reused (free),
        uncached lines fall back to the gTTS draft voice for timing."""
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.offline = offline
        super().__init__(**kwargs)
        self._fallback = GTTSService(lang="en", tld="com", cache_dir=self.cache_dir) if offline else None

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        cache_dir = Path(cache_dir or self.cache_dir)
        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "elevenlabs",
            "config": {"voice_id": self.voice_id, "model": self.model, "settings": VOICE_SETTINGS,
                       "timestamps": True},
        }
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        if self.offline:
            logger.info(f"Not cached, using draft voice for timing: {input_text[:40]}...")
            return self._fallback.generate_from_text(text, cache_dir=cache_dir, path=path, **kwargs)

        audio_path = str(path) if path else self.get_audio_basename(input_data) + ".mp3"
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/with-timestamps",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            json={"text": input_text, "model_id": self.model, "voice_settings": VOICE_SETTINGS},
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"ElevenLabs error {resp.status_code}: {resp.text[:300]}")
        body = resp.json()
        out = cache_dir / audio_path
        out.write_bytes(base64.b64decode(body["audio_base64"]))
        # Per-character timings drive the word-synced captions (see captions.py).
        out.with_suffix(".align.json").write_text(json.dumps(body["alignment"]))
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}


def get_voice() -> SpeechService:
    """REELEARN_VOICE: elevenlabs (default when a key is set) | offline | draft."""
    mode = os.getenv("REELEARN_VOICE", "auto").lower()
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    if mode == "offline":
        logger.info("Narration: offline (cached ElevenLabs lines, gTTS timing for the rest, no API calls)")
        return ElevenLabsTTS(api_key=key, voice_id=voice_id, offline=True)
    if mode != "draft" and key:
        logger.info(f"Narration: ElevenLabs voice {voice_id}")
        return ElevenLabsTTS(api_key=key, voice_id=voice_id)
    if mode == "elevenlabs":
        raise RuntimeError("REELEARN_VOICE=elevenlabs but ELEVENLABS_API_KEY is not set. See README.")
    logger.warning("Narration: gTTS draft voice (set ELEVENLABS_API_KEY for the real one)")
    return GTTSService(lang="en", tld="com")
