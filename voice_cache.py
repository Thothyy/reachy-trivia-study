"""Maps each fixed spoken line to a pre-rendered MP3 under assets/voice/.

The clips are rendered once (run prerender_voice.py on a machine that can reach
the internet) with the edge-tts neural voice and committed to the repo. At run
time the robot plays the natural voice straight from these files, so the study
laptop needs no internet and no connection to Microsoft's speech servers.

The filename is a hash of the voice + the exact text, so the renderer and the
robot agree on it without any lookup table. Change a line (or TTS_VOICE) and its
hash changes, so re-run prerender_voice.py to make the new clip.
"""
from __future__ import annotations

import hashlib

import config


def clip_path(text):
    """Return the committed-clip Path for a spoken line (voice + text -> file)."""
    key = hashlib.sha1(f"{config.TTS_VOICE}|{text}".encode("utf-8")).hexdigest()
    return config.VOICE_DIR / f"{key}.mp3"
