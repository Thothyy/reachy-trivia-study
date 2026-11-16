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

Setup (ID + condition) → 6 questions (each shown alone for 4s, then 4 options;
the three hint questions lock the options until Reachy finishes its spoken hint)
→ score + celebration button → Reachy's final request → 20s decision window →
data saved. A **"New participant"** button then resets the robot and returns to
setup for the next person.

**Reachy's gaze:** it looks at the **screen** while a question is read; on hint
questions it turns to the **participant** for the hint and holds there until they
answer, then looks back at the screen. On the game-over screen it faces the
participant for the request and, if the button is pressed, plays a built-in
**dance** (with its own music).

## Data

Saved to `data/` (git-ignored, stays on the laptop):
- `results.csv` — per participant: condition, score, **pressed_button**, **press_latency_s**.
- `participant_<id>_detail.csv` — per-question answer, correctness, time, hint given.

## Not in the app

The spoken briefing ("don't press the button"), the manipulation check, and the
Likert questionnaires are done **in person / on our own devices**.

## Editing

Tunables are at the top of `config.py`; the questions are in `questions.py`.

- **Timings** — `READ_SECONDS`, `HINT_DELAY_SECONDS`, `DECISION_SECONDS`.
- **Requests** — the two `FINAL_REQUEST` wordings (the only per-condition difference).
- **Gaze** — `GAZE_SCREEN_YAW` / `GAZE_PARTICIPANT_YAW` (tune to your table);
  set `GAZE_FLIP = True` if the two directions come out reversed; `GAZE_TRACKING`
  turns on experimental live face-following.
- **Dance** — `CELEBRATION_EMOTION` (`dance1` / `dance2` / `dance3`). Preview them
  with `python test_dances.py` and set your favourite.
- **Voice** — `TTS_VOICE` (see below).

**Voice.** Every line Reachy says is fixed, so it's **pre-rendered once and
played instantly** — no live text-to-speech lag during the study. By default the
clips are made at start-up with **edge-tts** (natural, needs internet, falls back
to the built-in Windows voice offline; browse voices with
`python -m edge_tts --list-voices`). For the best quality, run
`python prerender_voice.py` once with an ElevenLabs key to drop high-quality MP3s
into `assets/voice/` — the app uses those automatically if present.
