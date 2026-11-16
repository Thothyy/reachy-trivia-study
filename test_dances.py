"""Preview the celebration dance so I can check it on the robot before a session.

    python test_dances.py                 # plays the configured CELEBRATION_EMOTION
    python test_dances.py las-ketchup     # plays these move(s) by name
    python test_dances.py --list          # list every move in the dataset

Needs the daemon running (reachy-mini-daemon, or --sim for the simulation) and
the robot/sim connected. The move comes from CELEBRATION_EMOTION_DATASET in
config.py; the first run downloads that dataset from HuggingFace (needs internet
once), then it is cached. Once you've chosen, set CELEBRATION_EMOTION in
config.py to that name.
"""
from __future__ import annotations

import sys
import time

import config
from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import RecordedMoves


def main():
    moves = RecordedMoves(config.CELEBRATION_EMOTION_DATASET)
    args = sys.argv[1:]

    if args and args[0] in ("--list", "-l"):
        print(f"Moves in {config.CELEBRATION_EMOTION_DATASET}:")
        for name in sorted(moves.list_moves()):
            print("  ", name)
        return

    names = args or [config.CELEBRATION_EMOTION]
    with ReachyMini(connection_mode="localhost_only") as mini:
        for name in names:
            print(f"Playing {name} ...")
            try:
                mini.play_move(moves.get(name))        # motion + its own music
            except Exception as exc:
                print(f"  failed: {exc}")
            time.sleep(2.0)
    print("Done. Set CELEBRATION_EMOTION in config.py to your favourite.")


if __name__ == "__main__":
    main()
