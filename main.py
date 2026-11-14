"""Entry point for the trivia study.

Usage (with the virtual environment active):
    python main.py nobot      # no robot, just the UI -- for building and testing
    python main.py local      # simulation, or the Lite connected over USB
    python main.py wireless   # the wireless robot on the same network

I start the Reachy daemon separately first (see the README), then run this.
"""
from __future__ import annotations

import sys

from app import StudyApp
from robot import RobotController

VALID_TARGETS = {"nobot", "local", "wireless"}


def main():
    """Pick the robot target from the command line and launch the app."""
    target = sys.argv[1] if len(sys.argv) > 1 else "local"
    if target not in VALID_TARGETS:
        raise SystemExit(f"Use one of: {', '.join(sorted(VALID_TARGETS))}")
    robot = RobotController(target)
    app = StudyApp(robot)
    app.mainloop()


if __name__ == "__main__":
    main()
