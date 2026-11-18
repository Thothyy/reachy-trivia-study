# Reachy Mini Trivia — Reciprocity Study

*Version 3*

A trivia game with a **Reachy Mini** for an HRI study on **reciprocity**. The
participant answers ten multiple-choice questions while Reachy gives a spoken
hint on every one. At the end a **celebration button** appears (which they were told
not to press), and Reachy asks them to press it — **neutrally** or as a
**reciprocity appeal** ("I helped you earlier, press it in return?"). We log
whether they press it and how fast. Only the final request differs between
conditions; everything else is identical.

## Setup

You already have Python 3.12, uv and the Reachy SDK from Point-Look-Name, so
this is just a fresh venv for the UI libraries:

```bash
uv venv --python 3.12
```
```bash
.\.venv\Scripts\Activate.ps1
```
```bash
uv pip install -r requirements.txt
```

(macOS/Linux: activate with `source .venv/bin/activate`.)

## Run

`python main.py <target>` — `local` is the default.

| Mode | Commands |
|---|---|
| **No robot** (UI only) | `python main.py nobot` |
| **Simulation** (3D, no Lite) | `reachy-mini-daemon --sim --no-wake-up-on-start` → `python main.py` |
| **Physical Lite** (USB) | `reachy-mini-daemon --no-wake-up-on-start` → `python main.py` |

The setup screen shows the robot's connection status and has an **"Initialize
robot"** button: press it before a participant starts and Reachy turns to them,
says *"Hi, my name is Reachy, and I will help you with the trivia questions,"*
then faces forward. Quit with the window's ✕.

## Flow

Setup (ID + condition, optional **Initialize robot** greeting) → 10 questions
(each shown alone for 5s, then 4 options; every question locks the options until
Reachy finishes its spoken hint) → score + celebration button → Reachy's final
request → 20s decision window → data saved. A **"New participant"** button then
resets the robot and returns to setup for the next person.

**Reachy's gaze:** it looks **down at the laptop screen** while a question is
read, then turns to the **participant** for the hint and holds there until they
answer, before looking back at the screen. On the game-over screen it faces the
participant for the request and, if the button is pressed, plays the **Las
Ketchup** dance (with its music).

## Data

Everything lands in **one** file, `data/results.csv` (git-ignored, stays on the
laptop) — one row per session, with fixed column headers. Each row has the
condition and timestamps, how long the session took, the behavioural outcome
(**pressed_button** — defaults to `0` = not pressed — a **decision_status** of
`pressed` / `declined` / `incomplete`, and **press_latency_s** for pressers), the
trivia performance (score, accuracy, questions answered, hints given, mean
question time), the run's settings, and every question's choice, correctness,
time and hint in the `q1_…`, `q2_…` columns. The row is rewritten after **every
answer, at the decision, and when the window closes**, so a session closed early
still leaves its data behind (as `incomplete`, pressed `0`); a reused participant
ID adds a new row rather than overwriting. Pick whatever metrics you need later.

The questionnaire scales (reciprocity obligation, persuasiveness, legitimacy,
decision conflict) are collected separately and are **not** in this file.

## Not in the app

The spoken briefing ("don't press the button"), the manipulation check, and the
Likert questionnaires are done **in person / on our own devices**.

## Editing

Tunables are at the top of `config.py`; the questions are in `questions.py`.

- **Timings** — `READ_SECONDS`, `HINT_DELAY_SECONDS`, `DECISION_SECONDS`.
- **Requests** — the two `FINAL_REQUEST` wordings (the only per-condition difference).
- **Gaze** — `GAZE_SCREEN_YAW` / `GAZE_PARTICIPANT_YAW` (tune to your table);
  `GAZE_SCREEN_PITCH` tilts the head down onto the laptop screen (raise it if it
  still looks too high); set `GAZE_FLIP = True` if the two directions come out
  reversed; `GAZE_TRACKING` turns on experimental live face-following.
- **Dance** — `CELEBRATION_EMOTION` (default `las-ketchup`) from
  `CELEBRATION_EMOTION_DATASET`. Preview with `python test_dances.py` (or
  `--list` to see every move) and set your favourite. The first run downloads the
  dataset from HuggingFace, so the robot laptop needs internet once.
- **Voice** — `TTS_VOICE` (see below).

**Voice.** Reachy speaks with the natural **edge-tts** voice set by `TTS_VOICE`
(default `en-GB-SoniaNeural`). Because every line is fixed, the clips are
**pre-rendered and committed** under `assets/voice/`, so the study laptop plays
the natural voice straight from disk — **no internet needed during a session**
(handy when a campus/managed network blocks Microsoft's speech servers). If a
clip is missing it falls back to live edge-tts, then to the built-in Windows
voice. After changing a hint, a request, the greeting or `TTS_VOICE`, re-make the
clips on any machine with internet (a phone hotspot works) and commit them:

```bash
python prerender_voice.py
```

Browse voices with `python -m edge_tts --list-voices`.
