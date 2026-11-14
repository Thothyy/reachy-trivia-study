# Reachy Mini Trivia — Reciprocity Study

A trivia game with a **Reachy Mini** for an HRI study on **reciprocity**. The
participant answers six multiple-choice questions while Reachy gives three
spoken hints. At the end a **celebration button** appears (which they were told
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

The setup screen shows the robot's connection status. Quit with the window's ✕.

## Flow

Setup (ID + condition) → 6 questions (shown alone 4s, then 4 options; hint
questions lock until Reachy finishes its hint) → score + celebration button →
Reachy's request → 20s decision window → data saved.

## Data

Saved to `data/` (git-ignored, stays on the laptop):
- `results.csv` — per participant: condition, score, **pressed_button**, **press_latency_s**.
- `participant_<id>_detail.csv` — per-question answer, correctness, time, hint given.

## Not in the app

The spoken briefing ("don't press the button"), the manipulation check, and the
Likert questionnaires are done **in person / on our own devices**.

## Editing

Tunables (timings, the two request wordings) are at the top of `config.py`; the
questions are in `questions.py`.
