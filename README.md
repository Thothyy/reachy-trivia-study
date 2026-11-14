# Reachy Mini Trivia — Reciprocity Study

A trivia game run with a **Reachy Mini** robot, for a human–robot interaction
study on **reciprocity and persuasion**.

A participant answers six multiple-choice questions while Reachy gives three
scripted hints (establishing a small "favour"). At the end a **celebration
button** appears that the experimenter has told them *not* to press, and Reachy
makes a final request to press it — phrased either **neutrally** or as a
**reciprocity appeal** ("I helped you earlier, could you press it in return?").
The app records whether they press it and how quickly.

> It's the *wording of the final request* that differs between conditions.
> Everything else — questions, hints, movement, timing — is identical.

## How the session flows

1. **Setup screen** — the experimenter enters a participant ID and picks the
   condition (or "Auto" for a random one). The robot's connection status is shown.
2. **Six questions** — each is shown **alone for 4 seconds** to read, then it
   shrinks to the top and the **four options** appear. On the three hint
   questions the options stay locked while Reachy **says a hint out loud**, then
   unlock. Feedback is neutral ("Answer recorded. Let's continue.").
3. **Ending** — the score is shown with the **celebration button**. Reachy
   speaks its final request; the button then becomes pressable for **20 seconds**.
   Whether they press (and how fast) is logged, and a "you're free to leave"
   line appears below the button.

Throughout, Reachy makes small idle movements and little reactions so it feels
like part of the task.

---

## Setup (any laptop)

You need **Python 3.12** and **[uv](https://docs.astral.sh/uv/)** (a fast Python
installer). Install uv first if you don't have it:

```powershell
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, inside the project folder:

```bash
uv venv --python 3.12
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```
```bash
# macOS / Linux
source .venv/bin/activate
```

Install the dependencies:

```bash
uv pip install -r requirements.txt
```

> **Just want to see the app without a robot?** You can skip the Reachy SDK and
> install only the UI parts: `uv pip install customtkinter pillow numpy`, then
> run the "No robot" option below.

---

## Running it — three ways

The command is always `python main.py <target>`. `local` is the default.

### 1. No robot (just the UI — works on any laptop)

```bash
python main.py nobot
```

The full quiz runs on screen. Speech plays through the laptop speaker; there is
no movement. Great for reading questions, checking timing and the flow.

### 2. Simulation (see Reachy move in 3D — no physical robot needed)

Two terminals, environment activated in both. A MuJoCo 3D window appears.

```bash
reachy-mini-daemon --sim --no-wake-up-on-start
```
```bash
python main.py
```

### 3. Physical Reachy Mini Lite

Plug the Lite into the laptop with its **USB data cable** (and power). Then:

```bash
reachy-mini-daemon --no-wake-up-on-start
```
```bash
python main.py
```

The setup screen shows **"Robot connected"** once it's ready. Reachy speaks
through its own speaker (this needs GStreamer, part of the Reachy install; if it
isn't available, speech falls back to the laptop speaker — movement still works).

**To quit:** click the quiz window, then close it with the window's ✕ button.

---

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Entry point; picks the robot target (`nobot` / `local` / `wireless`). |
| `app.py` | The CustomTkinter UI and the whole study flow. |
| `robot.py` | `RobotController` — Reachy speech + gestures on a worker thread. |
| `questions.py` | The six questions as editable data (swap them freely). |
| `config.py` | Timings, the two conditions and the fixed wording. |
| `logger.py` | Writes the CSV data files. |
| `assets/` | Question images (flag, crest, script). |
| `data/` | Collected results (created on first run; git-ignored). |

## Where the data goes

Written to `data/` (kept out of git, so participant data stays on the laptop):

- `results.csv` — one row per participant: condition, trivia score,
  **pressed_button** (1 = pressed, 0 = not), **press_latency_s**.
- `participant_<id>_detail.csv` — each question's answer, correctness, response
  time and whether a hint was given.

## Done outside the app

To keep the study clean, these are **not** in the software:

- The **spoken briefing**, including "please do not press the celebration button"
  — the experimenter says this to the participant in person.
- The **manipulation check** ("Did Reachy mention it helped you?") and the
  **Likert questionnaires** (persuasiveness, reciprocity obligation, legitimacy,
  decision conflict) — filled in afterwards on one of our own devices.

## Tweaking

Most things live at the top of `config.py`: `READ_SECONDS`, `HINT_DELAY_SECONDS`,
`DECISION_SECONDS`, and the two `FINAL_REQUEST` wordings. The questions are in
`questions.py`.
