"""Render every fixed spoken line to a committed MP3 under assets/voice/.

Run this ONCE on any machine/network that can reach the edge-tts service (your
home Wi-Fi or a phone hotspot is fine -- it does not have to be the study
laptop):

    python prerender_voice.py

It renders each line from script_lines.spoken_lines() with the TTS_VOICE set in
config.py and saves it to assets/voice/<hash>.mp3. Commit that folder, and the
study laptop will play the natural voice offline -- no Bing connection needed.

Re-run it after changing a hint, a request, the greeting or TTS_VOICE; it skips
clips that already exist, so it only renders what is new.
"""
from __future__ import annotations

import asyncio

import edge_tts

import config
import voice_cache
from script_lines import spoken_lines


def main():
    config.VOICE_DIR.mkdir(parents=True, exist_ok=True)
    lines = spoken_lines()
    print(f"Rendering {len(lines)} line(s) with {config.TTS_VOICE} -> {config.VOICE_DIR}")

    made = skipped = 0
    for text in lines:
        path = voice_cache.clip_path(text)
        if path.exists() and path.stat().st_size > 0:
            skipped += 1
            continue
        asyncio.run(edge_tts.Communicate(text, config.TTS_VOICE).save(str(path)))
        if not path.exists() or path.stat().st_size == 0:
            raise SystemExit(f"edge-tts produced no audio for: {text!r}")
        made += 1
        print(f"  rendered: {text[:70]}")

    print(f"Done: {made} rendered, {skipped} already present, in {config.VOICE_DIR}")


if __name__ == "__main__":
    main()
