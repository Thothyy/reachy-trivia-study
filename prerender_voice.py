"""Pre-render every spoken line with ElevenLabs into assets/voice/.

The study script is fixed, so I render each line to an MP3 once, ahead of time.
The app then plays those files instantly -- best-quality voice, zero live
text-to-speech, no delay. Run this once (needs internet + an ElevenLabs key);
the generated clips can be committed so the whole group gets the same voice.

    # PowerShell
    $env:ELEVENLABS_API_KEY  = "sk_..."
    $env:ELEVENLABS_VOICE_ID = "the id of the voice you like"
    python prerender_voice.py

Find a voice's ID in your ElevenLabs account (Voices -> a voice -> "ID").
"""
from __future__ import annotations

import json
import os
import urllib.request

import config
from script_lines import clip_name, spoken_lines

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")
MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
OUT_DIR = config.ASSETS_DIR / "voice"


def render(text, path):
    """Call the ElevenLabs API and save the spoken `text` as an MP3 at `path`."""
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
           "?output_format=mp3_44100_128")
    body = json.dumps({"text": text, "model_id": MODEL_ID}).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    })
    with urllib.request.urlopen(request) as response:
        path.write_bytes(response.read())


def main():
    if not API_KEY or not VOICE_ID:
        raise SystemExit("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID first "
                         "(see the top of this file).")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = spoken_lines()
    for line in lines:
        destination = OUT_DIR / (clip_name(line) + ".mp3")
        print(f"Rendering: {line[:55]!r} -> {destination.name}")
        render(line, destination)
    print(f"Done - {len(lines)} clips written to {OUT_DIR}")


if __name__ == "__main__":
    main()
