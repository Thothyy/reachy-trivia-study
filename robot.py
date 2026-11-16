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
from script_lines import clip_name


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


def _clamp(value, limit):
    """Clamp a value to the range [-limit, limit]."""
    return max(-limit, min(limit, value))


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
        self._clips = {}                      # spoken line -> cached/pre-rendered audio path
        self._emotion_lib = None              # lazily loaded built-in emotion library
        self._tracking = threading.Event()    # set while the face-tracking loop runs
        self._gaze_active = False             # True while gaze (look/track) controls the head
        self._head_busy = False               # True while the worker is moving the head
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

    def prewarm(self, texts):
        """Pre-render all the given lines now, so they play instantly later."""
        self._jobs.put(("prewarm", list(texts), None, None))

    def play_emotion(self, name):
        """Queue a built-in Reachy emotion/dance from the Expressions library."""
        self._jobs.put(("emotion", name, None, None))

    def start_idle(self):
        """Allow small idle movements (used between questions)."""
        self._idle.set()

    def stop_idle(self):
        """Stop the idle movements (used while a question is on screen)."""
        self._idle.clear()

    def look_at(self, yaw, pitch=0.0):
        """Turn the head to a fixed yaw/pitch (degrees), e.g. toward the screen."""
        self._jobs.put(("look", (yaw, pitch), None, None))

    def start_tracking(self):
        """Turn to the participant and follow their face with the camera."""
        self._gaze_active = True
        if not self._tracking.is_set():
            self._tracking.set()
            threading.Thread(target=self._track_loop, daemon=True).start()

    def stop_tracking(self):
        """Stop following the participant's face."""
        self._tracking.clear()
        self._gaze_active = False

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
            if kind == "prewarm":
                for line in text:
                    try:
                        self._resolve(line)
                    except Exception:
                        pass
                if self._mini is not None and config.CELEBRATION_EMOTION:
                    try:
                        self._emotions()           # warm the emotion library too
                    except Exception:
                        pass
                continue
            if kind == "look":
                self._head_busy = True
                try:
                    self._do_look(text)
                finally:
                    self._head_busy = False
                continue
            self._head_busy = True
            try:
                if kind == "emotion":
                    self._do_emotion(text)
                elif kind == "say":
                    self._do_say(text, gesture, on_done)
                elif kind == "gesture":
                    self._do_gesture(text)
            finally:
                self._head_busy = False
        self._close()

    # -- speech ------------------------------------------------------------
    def _resolve(self, text):
        """Return a ready-to-play audio file for `text`: cached, pre-rendered or new.

        1. a clip already made this session (in-memory cache),
        2. a pre-rendered clip in assets/voice/ (e.g. made with ElevenLabs),
        3. a freshly synthesized clip (edge-tts, or the Windows voice offline),
           which is then cached so it is only ever made once.
        This is what keeps hints and the final request instant during the study.
        """
        if text in self._clips and os.path.exists(self._clips[text]):
            return self._clips[text]
        prerendered = config.ASSETS_DIR / "voice" / (clip_name(text) + ".mp3")
        if prerendered.exists():
            self._clips[text] = str(prerendered)
            return str(prerendered)
        path = self._synth(text)
        self._clips[text] = path
        return path

    def _do_say(self, text, gesture, on_done):
        """Play the line (robot speaker or laptop), with its gesture alongside."""
        path = self._resolve(text)
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

    # -- movement ----------------------------------------------------------
    def _emotions(self):
        """Lazily load the recorded-emotion library (cached after the first use)."""
        if self._emotion_lib is None:
            from reachy_mini.motion.recorded_move import RecordedMoves
            self._emotion_lib = RecordedMoves(config.CELEBRATION_EMOTION_DATASET)
        return self._emotion_lib

    def _do_emotion(self, name):
        """Play a named built-in emotion (motion + its own music) on the robot."""
        if self._mini is None:
            return
        try:
            move = self._emotions().get(name)
            self._mini.play_move(move)                # motion + sidecar sound
        except Exception as exc:
            print(f"[robot] emotion '{name}' failed ({exc}); using the simple dance")
            self._do_gesture(config.CELEBRATION_DANCE)

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
            elif name == "perk":                    # antennas only; the head stays where it is
                self._mini.goto_target(antennas=np.deg2rad([35, -35]), duration=0.4)
                self._mini.goto_target(antennas=np.zeros(2), duration=0.5)
        except Exception as exc:
            print(f"[robot] gesture error: {exc}")

    # -- gaze --------------------------------------------------------------
    def _do_look(self, target):
        """Turn the head to a fixed (yaw, pitch) in degrees."""
        yaw, pitch = target
        self._safe_goto(yaw, pitch, 0.6)

    def _safe_goto(self, yaw, pitch, duration):
        """goto_target to a head yaw/pitch (degrees), swallowing any error."""
        if self._mini is None:
            return
        try:
            from reachy_mini.utils import create_head_pose
            self._mini.goto_target(
                head=create_head_pose(yaw=yaw, pitch=pitch, degrees=True),
                duration=duration)
        except Exception:
            pass

    def _track_loop(self):
        """Follow the largest detected face by keeping it centred in the camera.

        The camera is on Reachy's head, so nudging the head toward the face keeps
        it centred -- a simple visual-servo loop. Falls back to just holding the
        participant direction if OpenCV or the robot camera is unavailable.
        """
        try:
            import cv2
        except Exception as exc:
            print(f"[gaze] OpenCV unavailable ({exc}); holding participant gaze")
            self._safe_goto(config.GAZE_PARTICIPANT_YAW, 0.0, 0.5)
            return
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        yaw, pitch = config.GAZE_PARTICIPANT_YAW, 0.0
        self._safe_goto(yaw, pitch, 0.5)                 # first, turn to the participant

        while self._tracking.is_set():
            frame = None
            if self._mini is not None:
                try:
                    frame = self._mini.media.get_frame()
                except Exception:
                    frame = None
            if frame is None:
                time.sleep(0.2)
                continue
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) if frame.ndim == 3 else frame
                faces = cascade.detectMultiScale(gray, 1.2, 5, minSize=(60, 60))
            except Exception:
                faces = []
            if len(faces):
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                rows, cols = gray.shape[:2]
                off_x = ((x + w / 2.0) - cols / 2.0) / (cols / 2.0)   # -1 .. 1
                off_y = ((y + h / 2.0) - rows / 2.0) / (rows / 2.0)
                if abs(off_x) > 0.12 or abs(off_y) > 0.12:       # deadzone avoids jitter
                    yaw = _clamp(yaw - config.GAZE_YAW_GAIN * off_x, config.GAZE_MAX_YAW)
                    pitch = _clamp(pitch + config.GAZE_PITCH_GAIN * off_y, config.GAZE_MAX_PITCH)
                    if not self._head_busy:
                        self._safe_goto(yaw, pitch, 0.4)
            time.sleep(0.15)

    def _maybe_idle(self):
        """Occasionally make a small, gentle move so the robot looks alive."""
        if self._mini is None or not self._idle.is_set() or self._gaze_active:
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
                                   antennas=antennas, duration=0.8)
        except Exception:
            pass

    def _close(self):
        """Release the SDK connection and delete this session's temp clips."""
        tmp = tempfile.gettempdir()
        for path in self._clips.values():
            try:
                if path.startswith(tmp):
                    os.remove(path)
            except Exception:
                pass
        if self._mini is not None:
            try:
                self._mini.__exit__(None, None, None)
            except Exception:
                pass
