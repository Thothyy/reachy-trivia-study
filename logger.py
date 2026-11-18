"""Writes every app-side metric from each session into ONE CSV: data/results.csv.

One row per session (one run of the study), with a fixed set of column headers.
The row carries the condition and timestamps, how long the session took, the
behavioural outcome (whether the celebration button was pressed -- defaulting to
NO -- and, for pressers, how fast), the trivia performance, and -- spread across
q1_*, q2_*, ... columns -- every question with the choice, correctness, time and
whether a hint was given. The questionnaire scales are collected separately and
are not part of this file.

The row is (re)written after every answer, at the decision, and when the window
closes, so a session that is closed early still leaves its data behind (marked
`incomplete`, pressed = 0). Each run gets a unique session_id, so re-using a
participant ID adds a new row rather than overwriting the old one.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime
from pathlib import Path

import config
from questions import QUESTIONS

RESULTS_FILE = "results.csv"

# Session-level columns, then one block of these per question (q1_id, q1_text…).
SESSION_FIELDS = [
    "session_id", "participant_id", "condition",
    "started_at", "finished_at", "duration_s",
    "decision_status", "pressed_button", "press_latency_s",
    "trivia_score", "num_questions", "questions_answered", "accuracy",
    "num_hints_given", "mean_question_time_s",
    "read_seconds", "hint_delay_seconds", "decision_seconds",
    "tts_voice", "celebration_emotion",
]
_PER_QUESTION = ["id", "text", "chosen", "correct_answer", "is_correct",
                 "seconds", "hint_given"]


def _fieldnames():
    """Full column list: the session fields plus q{n}_* for every question."""
    cols = list(SESSION_FIELDS)
    for i in range(1, len(QUESTIONS) + 1):
        cols.extend(f"q{i}_{name}" for name in _PER_QUESTION)
    return cols


class ParticipantLogger:
    """Collects one session's data and keeps its row in the single master CSV."""

    def __init__(self, data_dir, participant_id, condition):
        """Start a record for one run of the study.

        Args:
            data_dir: Folder where results.csv lives (created if missing).
            participant_id: The ID typed on the setup screen.
            condition: "neutral" or "reciprocity".
        """
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self.participant_id = participant_id
        self.condition = condition
        self.started_at = datetime.now()
        # Unique per run, so a repeated participant ID gets its own row and
        # repeated saves update THIS row instead of adding duplicates.
        self.session_id = f"{self.started_at:%Y%m%d-%H%M%S-%f}-{participant_id}"
        self._answers = []              # one dict per answered question, in order
        self.score = 0
        # Button outcome defaults to "not pressed"; the 20-second window turns it
        # into a deliberate "declined", a press turns it into "pressed".
        self.pressed = False
        self.press_latency_s = None
        self.decision_status = "incomplete"   # -> "pressed" / "declined" / stays incomplete

    # -- recording (each one saves, so a cut-short session is never lost) ---
    def record_answer(self, question_id, chosen, correct, seconds, hint_given):
        """Store one question's result, keep the running score, and save."""
        self._answers.append({
            "id": question_id,
            "chosen": chosen,
            "is_correct": int(correct),
            "seconds": round(seconds, 2),
            "hint_given": int(hint_given),
        })
        if correct:
            self.score += 1
        self.save()

    def record_decision(self, pressed, latency_s):
        """Store the celebration-button outcome (pressed + how fast), and save."""
        self.pressed = bool(pressed)
        self.press_latency_s = None if latency_s is None else round(latency_s, 2)
        self.decision_status = "pressed" if pressed else "declined"
        self.save()

    def finalize(self):
        """Persist a final row when the window closes or a new participant starts.

        If the session never reached a resolved decision it is saved as it stands
        (pressed = 0, status = incomplete), so closing the window still logs it.
        """
        self.save()

    # -- writing -----------------------------------------------------------
    def _row(self):
        """Build this session's full row (every question column included)."""
        finished = datetime.now()
        answered = len(self._answers)
        times = [a["seconds"] for a in self._answers]
        n = len(QUESTIONS)
        row = {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "condition": self.condition,
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "finished_at": finished.isoformat(timespec="seconds"),
            "duration_s": round((finished - self.started_at).total_seconds(), 2),
            "decision_status": self.decision_status,
            "pressed_button": int(self.pressed),                     # default 0 = no
            "press_latency_s": "" if self.press_latency_s is None else self.press_latency_s,
            "trivia_score": self.score,
            "num_questions": n,
            "questions_answered": answered,
            "accuracy": round(self.score / n, 3) if n else "",
            "num_hints_given": sum(a["hint_given"] for a in self._answers),
            "mean_question_time_s": round(sum(times) / len(times), 2) if times else "",
            "read_seconds": config.READ_SECONDS,
            "hint_delay_seconds": config.HINT_DELAY_SECONDS,
            "decision_seconds": config.DECISION_SECONDS,
            "tts_voice": config.TTS_VOICE,
            "celebration_emotion": config.CELEBRATION_EMOTION,
        }
        # The question itself is always known; answer columns fill in as answered.
        for i, q in enumerate(QUESTIONS, 1):
            row[f"q{i}_id"] = q["id"]
            row[f"q{i}_text"] = q["text"]
            row[f"q{i}_correct_answer"] = q["answer"]
            row[f"q{i}_chosen"] = ""
            row[f"q{i}_is_correct"] = ""
            row[f"q{i}_seconds"] = ""
            row[f"q{i}_hint_given"] = ""
        pos = {q["id"]: i for i, q in enumerate(QUESTIONS, 1)}
        for ans in self._answers:
            i = pos.get(ans["id"])
            if i:
                row[f"q{i}_chosen"] = ans["chosen"]
                row[f"q{i}_is_correct"] = ans["is_correct"]
                row[f"q{i}_seconds"] = ans["seconds"]
                row[f"q{i}_hint_given"] = ans["hint_given"]
        return row

    def save(self):
        """Rewrite data/results.csv with this session's row replacing any earlier
        version of it, keeping every other session's row and the fixed headers."""
        path = self._dir / RESULTS_FILE
        others = []
        if path.exists():
            try:
                with open(path, newline="", encoding="utf-8") as handle:
                    others = [r for r in csv.DictReader(handle)
                              if r.get("session_id") != self.session_id]
            except Exception:
                others = []
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=_fieldnames(),
                                    extrasaction="ignore")
            writer.writeheader()
            for r in others:
                writer.writerow(r)
            writer.writerow(self._row())


def _summary_rows(data_dir):
    """Yield the rows already saved in results.csv (empty if none yet)."""
    path = Path(data_dir) / RESULTS_FILE
    if not path.exists():
        return
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            yield from csv.DictReader(handle)
    except Exception:
        return


def balanced_condition(data_dir, conditions):
    """Pick the condition with the fewest saved sessions so far (ties random).

    Keeps the two groups close to even without assigning them by hand.
    """
    counts = {c: 0 for c in conditions}
    for row in _summary_rows(data_dir):
        if row.get("condition") in counts:
            counts[row["condition"]] += 1
    fewest = min(counts.values())
    return random.choice([c for c in conditions if counts[c] == fewest])


def participant_has_data(data_dir, participant_id):
    """Return True if this participant ID already has a row in results.csv."""
    return any(row.get("participant_id") == participant_id
               for row in _summary_rows(data_dir))
