"""Talks to Reachy Mini: speech (through the robot's speaker) plus gestures.

I run every robot command on one background thread (fed by a queue) so the
window never freezes and one action never overlaps another -- the same pattern
that worked for my point-and-name project.

Speech: I render each line to a short WAV with the built-in Windows voice, then
play it through the robot's own speaker (mini.media.play_sound). If the robot or
its audio is not available (e.g. "nobot" testing), I fall back to the laptop
speaker. Either way the robot's gesture plays alongside the speech.

Set the target to "nobot" to run the whole study UI with no robot at all.
"""
from __future__ import annotations

import os
import queue
import subprocess
import tempfile
import threading
import time
import wave

import numpy as np

import config


# Celebration dances: each is a list of pose steps played in order when the
# celebration button is pressed. Angles are in degrees; "ant" is the two antenna
# angles, "body" is the body yaw, "dur" is that step's duration in seconds.
DANCES = {
    # A swaying little spin, antennas swinging.
    "spin": [
        {"body": 25, "yaw": 10, "ant": (40, -40), "dur": 0.45},
        {"body": -25, "yaw": -10, "ant": (-40, 40), "dur": 0.45},
        {"body": 25, "yaw": 10, "ant": (40, -40), "dur": 0.45},
        {"body": -25, "yaw": -10, "ant": (-40, 40), "dur": 0.45},
        {"dur": 0.5},
    ],
    # Nodding to a beat, antennas bouncing.
    "bop": [
        {"pitch": 14, "ant": (30, 30), "dur": 0.28},
        {"pitch": -6, "ant": (-10, -10), "dur": 0.28},
        {"pitch": 14, "ant": (30, 30), "dur": 0.28},
        {"pitch": -6, "ant": (-10, -10), "dur": 0.28},
        {"pitch": 14, "ant": (30, 30), "dur": 0.28},
        {"dur": 0.4},
    ],
    # Head rolling side to side with a body sway.
    "wiggle": [
        {"roll": 16, "body": 12, "ant": (35, -35), "dur": 0.33},
        {"roll": -16, "body": -12, "ant": (-35, 35), "dur": 0.33},
        {"roll": 16, "body": 12, "ant": (35, -35), "dur": 0.33},
        {"roll": -16, "body": -12, "ant": (-35, 35), "dur": 0.33},
        {"dur": 0.4},
    ],
    # "Arms up" cheer: look up, antennas high, a couple of happy turns.
    "cheer": [
        {"pitch": -16, "ant": (55, 55), "dur": 0.4},
        {"pitch": -10, "yaw": 12, "ant": (40, 40), "dur": 0.3},
        {"pitch": -10, "yaw": -12, "ant": (40, 40), "dur": 0.3},
        {"pitch": -16, "ant": (55, 55), "dur": 0.3},
        {"dur": 0.5},
    ],
}


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
        self._connect_done = False            # True once the connection attempt has run
        self._idle = threading.Event()        # set while small idle fidgets are allowed
        threading.Thread(target=self._worker, daemon=True).start()

    def status_text(self):
        """A short line for the setup screen describing the robot connection."""
        if self._target == "nobot":
            return "Test mode (no robot)"
        if not self._connect_done:
            return "Connecting to the robot…"
        if self._mini is not None:
            return "Robot connected"
        return "No robot found — start the daemon, then restart this app"

    # -- public API --------------------------------------------------------
    def say(self, text, gesture=None, on_done=None):
        """Queue a spoken line.

        Args:
            text: The sentence to speak.
            gesture: A gesture name to play alongside the speech, or None.
            on_done: A callback fired (from the worker thread) once the line has
                finished -- the app uses it to re-enable the answer buttons after
                a hint. Marshal it onto the UI thread yourself.
        """
        self._jobs.put(("say", text, gesture, on_done))

    def gesture(self, name):
        """Queue a named gesture on its own (e.g. 'hint', 'thinking', 'nod')."""
        self._jobs.put(("gesture", name, None, None))

    def start_idle(self):
        """Allow small idle movements (used between questions)."""
        self._idle.set()

    def stop_idle(self):
        """Stop the idle movements (used while a question is on screen)."""
        self._idle.clear()

    def shutdown(self):
        """Ask the worker to finish and release the robot."""
        self._jobs.put(("stop", None, None, None))

    # -- worker ------------------------------------------------------------
    def _connect(self):
        """Open the SDK connection for the chosen target, or None for 'nobot'.

        Media is left ON so the robot's speaker is available; the quiz does not
        use the camera, so there is no conflict.
        """
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
        self._connect_done = True

        while True:
            try:
                kind, text, gesture, on_done = self._jobs.get(timeout=0.5)
            except queue.Empty:
                self._maybe_idle()
                continue
            if kind == "stop":
                break
            if kind == "say":
                self._do_say(text, gesture, on_done)
            elif kind == "gesture":
                self._do_gesture(text)
        self._close()

    # -- speech ------------------------------------------------------------
    def _do_say(self, text, gesture, on_done):
        """Render the line, play it (robot speaker or laptop), gesture alongside."""
        path = self._synth(text)
        duration = self._estimate_seconds(text, path)
        start = time.time()

        used_robot = False
        if self._mini is not None:
            try:
                self._mini.media.play_sound(path)    # non-blocking on the robot
                used_robot = True
            except Exception as exc:
                print(f"[robot] robot audio failed ({exc}); using laptop speaker")

        if gesture:
            self._do_gesture(gesture)                # overlaps the audio

        if used_robot:
            remaining = duration - (time.time() - start)
            if remaining > 0:
                time.sleep(remaining)
        else:
            self._play_pc(path)                      # blocking laptop playback

        self._cleanup(path)
        if on_done:
            on_done()

    def _synth(self, text):
        """Make a speech file: a natural edge-tts MP3, or a SAPI WAV if that fails.

        edge-tts uses Microsoft's neural voices (TTS_VOICE in config) and needs
        internet. If it can't be reached I fall back to the offline built-in
        Windows voice, so speech is never lost -- just less natural.
        """
        try:
            return self._synth_edge(text)
        except Exception as exc:
            print(f"[robot] edge-tts unavailable ({exc}); using the built-in voice")
            return self._synth_sapi(text)

    @staticmethod
    def _synth_edge(text):
        """Render text to an MP3 with an edge-tts neural voice; return its path."""
        import asyncio
        import edge_tts
        path = os.path.join(tempfile.gettempdir(), f"reachy_tts_{time.time_ns()}.mp3")

        async def run():
            await edge_tts.Communicate(text, config.TTS_VOICE).save(path)

        asyncio.run(run())
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise RuntimeError("edge-tts produced no audio")
        return path

    @staticmethod
    def _synth_sapi(text):
        """Render text to a WAV with the built-in Windows voice; return its path."""
        path = os.path.join(tempfile.gettempdir(), f"reachy_tts_{time.time_ns()}.wav")
        safe = text.replace("'", " ")
        command = ("Add-Type -AssemblyName System.Speech; "
                   "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                   f"$s.SetOutputToWaveFile('{path}'); $s.Speak('{safe}'); $s.Dispose()")
        subprocess.run(["powershell", "-NoProfile", "-Command", command],
                       creationflags=subprocess.CREATE_NO_WINDOW)
        return path

    @staticmethod
    def _estimate_seconds(text, path):
        """Length of the clip: exact for a WAV, estimated from the text for an MP3."""
        if path.lower().endswith(".wav"):
            try:
                with wave.open(path, "rb") as handle:
                    return handle.getnframes() / float(handle.getframerate())
            except Exception:
                pass
        return max(1.5, len(text.split()) / 2.7 + 0.6)

    @staticmethod
    def _play_pc(path):
        """Play an MP3 or WAV on the laptop speaker via Windows MCI (blocks)."""
        try:
            import ctypes
            mci = ctypes.windll.winmm.mciSendStringW
            mci("close reachytts", None, 0, None)        # clear any previous clip
            if mci(f'open "{path}" alias reachytts', None, 0, None) != 0:
                raise RuntimeError("could not open the audio file")
            mci("play reachytts wait", None, 0, None)
            mci("close reachytts", None, 0, None)
        except Exception as exc:
            print(f"[robot] laptop audio failed: {exc}")

    @staticmethod
    def _cleanup(path):
        try:
            os.remove(path)
        except Exception:
            pass

    # -- movement ----------------------------------------------------------
    def _run_dance(self, name):
        """Play a celebration dance sequence, then settle back to neutral."""
        from reachy_mini.utils import create_head_pose
        for step in DANCES.get(name, DANCES["cheer"]):
            head = create_head_pose(roll=step.get("roll", 0),
                                    pitch=step.get("pitch", 0),
                                    yaw=step.get("yaw", 0), degrees=True)
            self._mini.goto_target(
                head=head,
                antennas=np.deg2rad(step.get("ant", (0, 0))),
                body_yaw=float(np.deg2rad(step.get("body", 0))),
                duration=step.get("dur", 0.4))

    def _do_gesture(self, name):
        """Play one of the fixed gestures. Silently does nothing without a robot."""
        if self._mini is None:
            return
        try:
            from reachy_mini.utils import create_head_pose
            if name in DANCES:                      # a celebration dance sequence
                self._run_dance(name)
                return
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
            elif name == "wave":                    # friendly hello wave (robot test)
                self._mini.goto_target(head=create_head_pose(yaw=10, degrees=True),
                                       antennas=np.deg2rad([45, 10]), duration=0.3)
                self._mini.goto_target(antennas=np.deg2rad([10, 45]), duration=0.3)
                self._mini.goto_target(antennas=np.deg2rad([45, 10]), duration=0.3)
                self._mini.goto_target(head=create_head_pose(),
                                       antennas=np.zeros(2), duration=0.4)
        except Exception as exc:
            print(f"[robot] gesture error: {exc}")

    def _maybe_idle(self):
        """Occasionally make a small, gentle move so the robot looks alive."""
        if self._mini is None or not self._idle.is_set():
            return
        if np.random.random() > 0.5:                # fidget about half the time
            return
        try:
            from reachy_mini.utils import create_head_pose
            yaw = float(np.random.uniform(-8, 8))
            pitch = float(np.random.uniform(-4, 4))
            antennas = np.deg2rad([np.random.uniform(-12, 12),
                                   np.random.uniform(-12, 12)])
            self._mini.goto_target(head=create_head_pose(yaw=yaw, pitch=pitch, degrees=True),
                                   antennas=antennas, duration=1.1)
        except Exception:
            pass

    def _close(self):
        """Release the SDK connection on shutdown."""
        if self._mini is not None:
            try:
                self._mini.__exit__(None, None, None)
            except Exception:
                pass
