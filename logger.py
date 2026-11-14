"""Writes one tidy CSV row per participant, plus a per-question detail file.

I log everything the analysis needs: the condition, each answer and how long it
took, whether a hint was given, the trivia score and -- the key outcome --
whether the celebration button was pressed and how quickly.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


class ParticipantLogger:
    """Collects one participant's data and appends it to the master CSV."""

    SUMMARY_FIELDS = [
        "participant_id", "condition", "started_at", "finished_at",
        "trivia_score", "pressed_button", "press_latency_s", "manipulation_answer",
    ]
    DETAIL_FIELDS = ["question_id", "chosen", "correct", "seconds", "hint_given"]

    def __init__(self, data_dir, participant_id, condition):
        """Start a record for one participant.

        Args:
            data_dir: Folder where the CSV files live (created if missing).
            participant_id: The ID I type on the setup screen.
            condition: "neutral" or "reciprocity".
        """
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self.participant_id = participant_id
        self.condition = condition
        self.started_at = datetime.now()
        self._answers = []              # one dict per question
        self.score = 0
        self.pressed = None             # True / False once the decision is made
        self.press_latency_s = None
        self.manipulation_answer = None

    def record_answer(self, question_id, chosen, correct, seconds, hint_given):
        """Store one question's result and keep the running score."""
        self._answers.append({
            "question_id": question_id,
            "chosen": chosen,
            "correct": int(correct),
            "seconds": round(seconds, 2),
            "hint_given": int(hint_given),
        })
        if correct:
            self.score += 1

    def record_decision(self, pressed, latency_s):
        """Store whether the celebration button was pressed, and how quickly."""
        self.pressed = pressed
        self.press_latency_s = None if latency_s is None else round(latency_s, 2)

    def record_manipulation(self, answer):
        """Store the answer to the 'did Reachy mention it helped you?' check."""
        self.manipulation_answer = answer

    def save(self):
        """Write the per-question detail file and append the summary row."""
        self._save_details()
        self._append_summary()

    # -- internals ---------------------------------------------------------
    def _save_details(self):
        path = self._dir / f"participant_{self.participant_id}_detail.csv"
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.DETAIL_FIELDS)
            writer.writeheader()
            writer.writerows(self._answers)

    def _append_summary(self):
        path = self._dir / "results.csv"
        row = {
            "participant_id": self.participant_id,
            "condition": self.condition,
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "trivia_score": self.score,
            "pressed_button": "" if self.pressed is None else int(self.pressed),
            "press_latency_s": "" if self.press_latency_s is None else self.press_latency_s,
            "manipulation_answer": self.manipulation_answer or "",
        }
        write_header = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.SUMMARY_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
