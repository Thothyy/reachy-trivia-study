"""The fixed set of lines Reachy ever speaks.

Because the script never changes, every line is rendered to audio once at
start-up (prewarm) and cached, so there is no live text-to-speech lag during
the study.
"""
from __future__ import annotations

import config
from questions import QUESTIONS

HINT_PREFIX = "Here's a hint for you. "


def spoken_lines():
    """Every line Reachy can say in a session, so they can all be pre-rendered."""
    lines = [HINT_PREFIX + q["hint"] for q in QUESTIONS if q["hint"]]
    lines.extend(config.FINAL_REQUEST.values())
    lines.append(config.INTRO_GREETING)      # the "Initialize robot" greeting
    lines.append("Woohoo!")                  # fallback celebration cheer
    return lines
