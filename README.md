# Reachy Mini Trivia — Reciprocity Study

A trivia game run with a Reachy Mini robot, for a human–robot interaction study
on **reciprocity and persuasion**. A participant answers six multiple-choice
questions while Reachy gives three scripted hints. At the end a *celebration
button* appears that the experimenter told them not to press, and Reachy makes a
final request to press it — phrased either **neutrally** or as a **reciprocity
appeal**. The app records whether they press it and how quickly.

> Private group project — not for distribution.

## What it does

- Experimenter setup screen (participant ID + condition).
- Briefing with a comprehension check ("do not press the celebration button").
- Six questions: each shown **alone for 8 s**, then the question shrinks and the
  four options appear; on the three hint questions Reachy speaks a scripted hint.
- Score screen → Reachy's final request (neutral vs. reciprocity) → the
  celebration button with a **20 s decision window**.
- Manipulation check, then a pointer to the external questionnaire.
- Logs one summary row per participant to `data/results.csv` plus a per-question
  detail file.

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Entry point; pick the robot target. |
| `app.py` | The CustomTkinter UI and the whole study flow. |
| `robot.py` | `RobotController` — Reachy speech + gestures on a worker thread. |
| `questions.py` | The six questions as editable data. |
| `config.py` | Timings, conditions and all fixed wording. |
| `logger.py` | Writes the CSV data files. |
| `assets/` | Question images (flag, crest, script). |
| `data/` | Collected results (git-ignored). |

## Setup

```powershell
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## Run

**Test with no robot** (any computer):

```powershell
python main.py nobot
```

**With the Reachy Mini Lite** (two terminals, venv active in both):

```powershell
reachy-mini-daemon --no-wake-up-on-start
```

```powershell
python main.py local
```

(The robot speaks through the computer's speaker and moves its head/antennas.
Use `wireless` instead of `local` for the wireless robot.)

## Data

- `data/results.csv` — one row per participant: condition, trivia score,
  **pressed_button** (1/0), **press_latency_s**, manipulation answer.
- `data/participant_<id>_detail.csv` — each question's answer, correctness,
  response time and whether a hint was given.

The Likert questionnaires (persuasiveness, reciprocity obligation, legitimacy,
decision conflict) are collected in a separate online form — see
`QUESTIONNAIRE_URL` in `config.py`.
