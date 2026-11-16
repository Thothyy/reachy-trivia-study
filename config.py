"""Central settings for the Reachy Mini trivia study.

I keep every timing, path and fixed piece of wording here so the experiment
stays identical between participants and I can tweak a number in one place.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Folders
# --------------------------------------------------------------------------- #
PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"     # question images (flags, crests, scripts)
DATA_DIR = PROJECT_DIR / "data"         # one results row per participant lands here

# --------------------------------------------------------------------------- #
# Conditions (the independent variable: how the FINAL request is phrased)
# --------------------------------------------------------------------------- #
NEUTRAL = "neutral"
RECIPROCITY = "reciprocity"
CONDITIONS = (NEUTRAL, RECIPROCITY)

# The ONLY thing that differs between conditions is this final spoken request.
FINAL_REQUEST = {
    NEUTRAL: ("We've finished the trivia game! I hope you enjoyed the questions "
              "earlier. Could you press the celebration button for me now, please?"),
    RECIPROCITY: ("We've finished the trivia game! I helped you with the questions "
                  "earlier. Could you press the celebration button for me in return, "
                  "please?"),
}

# --------------------------------------------------------------------------- #
# Timing (seconds)
# --------------------------------------------------------------------------- #
READ_SECONDS = 4            # question shown alone before the options appear
HINT_DELAY_SECONDS = 0.5    # after options appear, wait this long before a hint
DECISION_SECONDS = 20       # window to (not) press the celebration button
FEEDBACK_SECONDS = 1.3      # how long the neutral "answer recorded" line shows

# Built-in Reachy emotion played when the celebration button is pressed, from
# Reachy Mini Control's Expressions library (plays with its own music). Try
# "dance1", "dance2" or "dance3". Set CELEBRATION_EMOTION = "" to fall back to
# the simple hand-coded dance below instead.
CELEBRATION_EMOTION = "dance1"
CELEBRATION_EMOTION_DATASET = "pollen-robotics/reachy-mini-emotions-library"

# Hand-coded fallback dance (used only if CELEBRATION_EMOTION is "" or fails).
# Options: "cheer", "spin", "bop", "wiggle".
CELEBRATION_DANCE = "cheer"

# Natural neural voice for Reachy's speech (via edge-tts; needs internet). It
# falls back to the built-in Windows voice if edge-tts can't be reached.
# Browse voices with:  python -m edge_tts --list-voices
# Friendly options: en-GB-SoniaNeural, en-GB-RyanNeural, en-US-AriaNeural,
#                   en-US-GuyNeural, en-AU-NatashaNeural.
TTS_VOICE = "en-GB-SoniaNeural"

# --------------------------------------------------------------------------- #
# Gaze (where Reachy looks during the quiz)
# --------------------------------------------------------------------------- #
# Reachy sits to the participant's RIGHT (see the README diagram). While a
# question is read it looks toward the laptop/task; when the options appear it
# turns to the participant and (optionally) follows their face with its camera.
# Tune these yaw angles (degrees) to your table; flip a sign if it turns the
# wrong way. These are deliberately separate from FLIP_HEAD_DIRECTION so you can
# dial the gaze in on the day without touching the pointing logic.
GAZE_SCREEN_YAW = 30.0         # look toward the laptop/task while the question is read
GAZE_PARTICIPANT_YAW = -30.0   # base turn toward the participant when the options appear

GAZE_TRACKING = True           # False = just turn to the participant and hold (no camera)
GAZE_YAW_GAIN = 25.0           # how hard to turn toward the face; flip the sign if it turns away
GAZE_PITCH_GAIN = 12.0         # same, vertically
GAZE_MAX_YAW = 50.0            # never turn the head past +/- this
GAZE_MAX_PITCH = 18.0

# --------------------------------------------------------------------------- #
# Fixed wording (kept identical in both conditions)
# --------------------------------------------------------------------------- #
ANSWER_FEEDBACK = "Answer recorded. Let's continue."

# Note: the spoken briefing (incl. "do not press the celebration button"), the
# manipulation check and the Likert questionnaires are handled OUTSIDE the app --
# the experimenter briefs the participant in person, and the questionnaires are
# filled in afterwards on one of our own devices.
