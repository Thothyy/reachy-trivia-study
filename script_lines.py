"""The fixed set of lines Reachy ever speaks, plus a stable filename for each.

Because the script never changes, every line can be rendered to audio once --
either pre-cached at start-up (edge-tts) or pre-rendered with ElevenLabs into
assets/voice/ -- and then played instantly during the study. That is what
removes the live text-to-speech delay.
"""
from __future__ import annotations

import re

import config
from questions import QUESTIONS

HINT_PREFIX = "Here is a hint. "


def clip_name(text):
    """A stable, readable filename stem for a spoken line (no extension)."""
    stem = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return stem[:60]


def spoken_lines():
    """Every line Reachy can say in a session, so they can all be pre-rendered."""
    lines = [HINT_PREFIX + q["hint"] for q in QUESTIONS if q["hint"]]
    lines.extend(config.FINAL_REQUEST.values())
    lines.append("Woohoo!")
    lines.append("Hello! I am ready.")
    return lines
