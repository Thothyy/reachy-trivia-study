"""Talks to Reachy Mini: speech plus a small set of gestures.

I run every robot command on one background thread (fed by a queue) so the
window never freezes and one action never overlaps another -- the same pattern
that worked for my point-and-name project. Speech uses the built-in Windows
voice in a fresh process, which does not fall silent after repeated use.

Set the target to "nobot" to run the whole study UI with no robot at all, which
is how I build and test the flow on any computer.
"""
from __future__ import annotations

import queue
import subprocess
import threading
import time

import numpy as np


def speak(text):
    """Say a line aloud with the built-in Windows voice (blocks until done).

    Args:
        text: The sentence to speak.
    """
    safe = text.replace("'", " ")                       # keep the PowerShell string simple
    command = ("Add-Type -AssemblyName System.Speech; "
               "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
               f".Speak('{safe}')")
    subprocess.run(["powershell", "-NoProfile", "-Command", command],
                   creationflags=subprocess.CREATE_NO_WINDOW)


class RobotController:
    """Owns the Reachy Mini connection and turns requests into speech + moves.

    The study needs identical movement and voice in both conditions, so the
    gestures here are the same for everyone. Only the words of the final request
    change, and that text is chosen by the app, not here.
    """

    def __init__(self, target="nobot"):
        """Create the controller and start its background worker.

        Args:
            target: "nobot" (no robot, for testing), "local" (simulation or the
                Lite over USB) or "wireless" (the wireless robot on the network).
        """
        self._target = target
        self._jobs = queue.Queue()
        self._mini = None
        self._idle = threading.Event()        # set while small idle fidgets are allowed
        threading.Thread(target=self._worker, daemon=True).start()

    # -- public API --------------------------------------------------------
    def say(self, text, gesture=None):
        """Queue a spoken line, optionally with a gesture played alongside it."""
        self._jobs.put(("say", text, gesture))

    def gesture(self, name):
        """Queue a named gesture on its own (e.g. 'hint', 'thinking', 'nod')."""
        self._jobs.put(("gesture", name, None))

    def start_idle(self):
        """Allow small idle movements (used between questions)."""
        self._idle.set()

    def stop_idle(self):
        """Stop the idle movements (used while a question is on screen)."""
        self._idle.clear()

    def shutdown(self):
        """Ask the worker to finish and release the robot."""
        self._jobs.put(("stop", None, None))

    # -- internals ---------------------------------------------------------
    def _connect(self):
        """Open the SDK connection for the chosen target, or None for 'nobot'."""
        if self._target == "nobot":
            return None
        from reachy_mini import ReachyMini
        if self._target == "wireless":
            return ReachyMini(connection_mode="network", host="reachy-mini.local")
        return ReachyMini(connection_mode="localhost_only")   # simulation or Lite

    def _worker(self):
        """Process one job at a time; fidget a little when idle (runs forever)."""
        try:
            self._mini = self._connect()
            print(f"[robot] connected ({self._target})")
        except Exception as exc:
            print(f"[robot] could not connect ({exc}); running without movement")
            self._mini = None

        while True:
            try:
                kind, text, gesture = self._jobs.get(timeout=0.5)
            except queue.Empty:
                self._maybe_idle()
                continue
            if kind == "stop":
                break
            if kind == "say":
                self._do_say(text, gesture)
            elif kind == "gesture":
                self._do_gesture(text)
        self._close()

    def _do_say(self, text, gesture):
        """Speak on a sub-thread so a slow gesture can never cut the speech off."""
        speaker = threading.Thread(target=speak, args=(text,), daemon=True)
        speaker.start()
        if gesture:
            self._do_gesture(gesture)
        speaker.join()

    def _do_gesture(self, name):
        """Play one of the fixed gestures. Silently does nothing without a robot."""
        if self._mini is None:
            return
        try:
            from reachy_mini.utils import create_head_pose
            if name == "hint":                      # lean in, perk antennas (sharing a tip)
                self._mini.goto_target(head=create_head_pose(pitch=12, degrees=True),
                                       antennas=np.deg2rad([35, -35]), duration=0.5)
                self._mini.goto_target(head=create_head_pose(),
                                       antennas=np.zeros(2), duration=0.6)
            elif name == "thinking":                # a small tilt, as if considering
                self._mini.goto_target(head=create_head_pose(roll=8, yaw=10, degrees=True),
                                       duration=0.6)
                self._mini.goto_target(head=create_head_pose(), duration=0.6)
            elif name == "request":                 # open, friendly nod for the final ask
                self._mini.goto_target(head=create_head_pose(pitch=-8, degrees=True),
                                       antennas=np.deg2rad([20, -20]), duration=0.5)
                self._mini.goto_target(head=create_head_pose(),
                                       antennas=np.zeros(2), duration=0.6)
            elif name == "nod":                     # quick acknowledgement
                self._mini.goto_target(head=create_head_pose(pitch=10, degrees=True),
                                       duration=0.3)
                self._mini.goto_target(head=create_head_pose(), duration=0.3)
        except Exception as exc:
            print(f"[robot] gesture error: {exc}")

    def _maybe_idle(self):
        """Occasionally make a tiny head turn so the robot does not look frozen."""
        if self._mini is None or not self._idle.is_set():
            return
        if np.random.random() > 0.35:               # only fidget sometimes
            return
        try:
            from reachy_mini.utils import create_head_pose
            yaw = float(np.random.uniform(-7, 7))
            self._mini.goto_target(head=create_head_pose(yaw=yaw, degrees=True), duration=1.2)
        except Exception:
            pass

    def _close(self):
        """Release the SDK connection on shutdown."""
        if self._mini is not None:
            try:
                self._mini.__exit__(None, None, None)
            except Exception:
                pass
