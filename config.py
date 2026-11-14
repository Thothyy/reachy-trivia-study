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
READ_SECONDS = 8            # question shown alone before the options appear
HINT_DELAY_SECONDS = 1.5    # after options appear, wait this long before a hint
DECISION_SECONDS = 20       # window to (not) press the celebration button
FEEDBACK_SECONDS = 1.3      # how long the neutral "answer recorded" line shows

# --------------------------------------------------------------------------- #
# Fixed wording (kept identical in both conditions)
# --------------------------------------------------------------------------- #
ANSWER_FEEDBACK = "Answer recorded. Let's continue."

BRIEFING_TEXT = (
    "You will play a short trivia game with Reachy Mini, who will give you a few "
    "hints along the way. Each correct answer earns one point.\n\n"
    "At the end, a celebration button will appear on the screen. It is part of a "
    "separate feature we are not using today. Please do NOT press the celebration "
    "button, even after the game ends."
)
COMPREHENSION_PROMPT = "I understand that I should not press the celebration button."

MANIPULATION_QUESTION = "Did Reachy mention that it had helped you earlier?"
MANIPULATION_OPTIONS = ("Yes", "No", "Unsure")

# Shown at the very end; point participants to the external Likert questionnaire.
QUESTIONNAIRE_URL = "https://forms.gle/REPLACE_ME"
