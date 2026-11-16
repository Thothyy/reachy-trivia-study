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
READ_SECONDS = 5            # question shown alone before the options appear
HINT_DELAY_SECONDS = 0.5    # after options appear, wait this long before a hint
DECISION_SECONDS = 20       # window to (not) press the celebration button
FEEDBACK_SECONDS = 1.3      # how long the neutral "answer recorded" line shows

# Recorded dance played when the celebration button is pressed (plays with its
# own music). "las-ketchup" is choreographed to the Las Ketchup song and lives in
# the community "Anne-Charlotte/music" library you can see in Reachy Mini Control.
# The first run downloads that dataset from HuggingFace (needs internet once),
# then it is cached. Preview moves with  python test_dances.py --list  /
# python test_dances.py <name>.  Set CELEBRATION_EMOTION = "" to fall back to the
# simple hand-coded dance below instead.
CELEBRATION_EMOTION = "las-ketchup"
CELEBRATION_EMOTION_DATASET = "Anne-Charlotte/music"

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
GAZE_SCREEN_PITCH = 15.0       # tilt the head DOWN this many degrees when looking at the
                               # laptop (the screen sits below eye level); raise it if Reachy
                               # still looks too high, lower/0 for level. Participant gaze stays level.
GAZE_PARTICIPANT_YAW = -30.0   # base turn toward the participant when the options appear
GAZE_FLIP = False              # set True if the two directions are reversed (looks at the screen when it should look at you)

GAZE_TRACKING = False          # True = actively follow the face (experimental); False = turn and hold steady (recommended)
GAZE_YAW_GAIN = 25.0           # how hard to turn toward the face; flip the sign if it turns away
GAZE_PITCH_GAIN = 12.0         # same, vertically
GAZE_MAX_YAW = 50.0            # never turn the head past +/- this
GAZE_MAX_PITCH = 18.0

# --------------------------------------------------------------------------- #
# Fixed wording (kept identical in both conditions)
# --------------------------------------------------------------------------- #
ANSWER_FEEDBACK = "Answer recorded. Let's continue."

# Spoken once when the experimenter presses "Initialize robot" on the setup screen:
# Reachy turns to the participant, introduces itself, then faces forward.
INTRO_GREETING = "Hi, my name is Reachy, and I will help you with the trivia questions."

# Note: the spoken briefing (incl. "do not press the celebration button"), the
# manipulation check and the Likert questionnaires are handled OUTSIDE the app --
# the experimenter briefs the participant in person, and the questionnaires are
# filled in afterwards on one of our own devices.
