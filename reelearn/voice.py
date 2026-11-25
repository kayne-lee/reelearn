"""Narration voices.

`get_voice()` picks the speech service:
  - ElevenLabs when ELEVENLABS_API_KEY is set (in .env or the environment)
  - gTTS (free, robotic) otherwise, or when REELEARN_VOICE=draft

Audio is cached under media/voiceovers/, keyed by text + voice + model,
so re-rendering an unchanged line never calls the API again.
"""
from __future__ import annotations

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
VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 0.15,
    "use_speaker_boost": True,
}


class ElevenLabsTTS(SpeechService):
    """Minimal ElevenLabs service using the current REST API."""

    def __init__(self, api_key: str, voice_id: str, model: str = DEFAULT_MODEL, **kwargs):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        super().__init__(**kwargs)

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        cache_dir = Path(cache_dir or self.cache_dir)
        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "elevenlabs",
            "config": {"voice_id": self.voice_id, "model": self.model, "settings": VOICE_SETTINGS},
        }
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached

        audio_path = str(path) if path else self.get_audio_basename(input_data) + ".mp3"
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            json={"text": input_text, "model_id": self.model, "voice_settings": VOICE_SETTINGS},
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"ElevenLabs error {resp.status_code}: {resp.text[:300]}")
        (cache_dir / audio_path).write_bytes(resp.content)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}


def get_voice() -> SpeechService:
    mode = os.getenv("REELEARN_VOICE", "auto").lower()
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if mode != "draft" and key:
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
        logger.info(f"Narration: ElevenLabs voice {voice_id}")
        return ElevenLabsTTS(api_key=key, voice_id=voice_id)
    if mode == "elevenlabs":
        raise RuntimeError("REELEARN_VOICE=elevenlabs but ELEVENLABS_API_KEY is not set. See README.")
    logger.warning("Narration: gTTS draft voice (set ELEVENLABS_API_KEY for the real one)")
    return GTTSService(lang="en", tld="com")
