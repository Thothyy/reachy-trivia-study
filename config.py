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
HINT_DELAY_SECONDS = 1.5    # after options appear, wait this long before a hint
DECISION_SECONDS = 20       # window to (not) press the celebration button
FEEDBACK_SECONDS = 1.3      # how long the neutral "answer recorded" line shows

# Celebration dance played when the button is pressed (same in both conditions).
# Options: "cheer", "spin", "bop", "wiggle".
CELEBRATION_DANCE = "cheer"

# --------------------------------------------------------------------------- #
# Fixed wording (kept identical in both conditions)
# --------------------------------------------------------------------------- #
ANSWER_FEEDBACK = "Answer recorded. Let's continue."

# Note: the spoken briefing (incl. "do not press the celebration button"), the
# manipulation check and the Likert questionnaires are handled OUTSIDE the app --
# the experimenter briefs the participant in person, and the questionnaires are
# filled in afterwards on one of our own devices.
