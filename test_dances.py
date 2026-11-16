"""Play the built-in dance emotions so I can pick my favourite for the celebration.

    python test_dances.py            # plays dance1, dance2, dance3 in turn
    python test_dances.py dance2     # plays just that one

Needs the daemon running (reachy-mini-daemon, or --sim for the simulation) and
the robot/sim connected. Once you've chosen, set CELEBRATION_EMOTION in
config.py to that name.
"""
from __future__ import annotations

import sys
import time

import config
from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import RecordedMoves

DANCES = ["dance1", "dance2", "dance3"]


def main():
    names = sys.argv[1:] or DANCES
    moves = RecordedMoves(config.CELEBRATION_EMOTION_DATASET)
    with ReachyMini(connection_mode="localhost_only") as mini:
        for name in names:
            print(f"Playing {name} ...")
            try:
                mini.play_move(moves.get(name))
            except Exception as exc:
                print(f"  failed: {exc}")
            time.sleep(2.0)
    print("Done. Set CELEBRATION_EMOTION in config.py to your favourite.")


if __name__ == "__main__":
    main()
