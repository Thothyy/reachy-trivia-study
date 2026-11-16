"""The study UI and flow, built with CustomTkinter.

I drive the whole session from here: the experimenter setup screen, the briefing
with its comprehension check, the six trivia questions (each shown alone for a
few seconds before the options appear), the celebration-button decision, and the
manipulation check. Reachy's speech and gestures are triggered at the right
moments through the RobotController.

Everything runs in one process, so when a question appears I can trigger Reachy
in the same breath -- that is what makes the robot feel part of the task.
"""
from __future__ import annotations

import time

import customtkinter as ctk

import config
from logger import ParticipantLogger, balanced_condition, participant_has_data
from questions import QUESTIONS
from script_lines import spoken_lines, HINT_PREFIX

try:                                 # Pillow is only needed for the image questions
    from PIL import Image
except ImportError:
    Image = None


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# A small, consistent palette so the screens feel like one system.
BG = "#14151a"
CARD = "#1d1f27"
ACCENT = "#4f8cff"
CELEBRATE = "#ff5c8a"
TEXT_DIM = "#9aa0ad"


class StudyApp(ctk.CTk):
    """The top-level window; it swaps one screen frame for the next."""

    def __init__(self, robot):
        """Build the window and show the experimenter setup screen.

        Args:
            robot: A RobotController (its target may be "nobot" for testing).
        """
        super().__init__()
        self.robot = robot
        self.robot.prewarm(spoken_lines())   # render all speech up front -> instant playback
        self.title("Reachy Mini Trivia")
        self.geometry("1040x720")
        self.minsize(860, 620)
        self.configure(fg_color=BG)

        self._container = ctk.CTkFrame(self, fg_color=BG)
        self._container.pack(fill="both", expand=True)

        # Session state.
        self.logger = None
        self.condition = None
        self._q_index = 0
        self._q_enabled_at = 0.0         # when the options became clickable
        self._hint_given = False
        self._image_ref = None           # keep a reference so the image is not GC'd
        self._decision_start = 0.0
        self._option_buttons = []        # the four answer buttons for this question
        self._dup_pid = None             # a participant ID the user confirmed re-using

        # Pending timers I may need to cancel on a screen change.
        self._timers = []

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._show_setup()

    # ------------------------------------------------------------------ #
    # Small helpers
    # ------------------------------------------------------------------ #
    def _after(self, seconds, callback):
        """Schedule a callback and remember it so I can cancel it on a change."""
        handle = self.after(int(seconds * 1000), callback)
        self._timers.append(handle)
        return handle

    def _cancel_timers(self):
        """Cancel every pending timer (called whenever I swap screens)."""
        for handle in self._timers:
            try:
                self.after_cancel(handle)
            except Exception:
                pass
        self._timers = []

    def _clear(self):
        """Cancel timers and remove the current screen's widgets."""
        self._cancel_timers()
        for child in self._container.winfo_children():
            child.destroy()

    def _card(self):
        """Return a centred rounded card to put a screen's contents in."""
        card = ctk.CTkFrame(self._container, fg_color=CARD, corner_radius=20)
        card.place(relx=0.5, rely=0.5, anchor="center")
        return card

    def _on_close(self):
        self.robot.stop_tracking()
        self.robot.shutdown()
        self.destroy()

    # ------------------------------------------------------------------ #
    # 1. Experimenter setup
    # ------------------------------------------------------------------ #
    def _show_setup(self):
        self._clear()
        card = self._card()

        ctk.CTkLabel(card, text="Reachy Mini Trivia",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(padx=60, pady=(40, 6))
        ctk.CTkLabel(card, text="Experimenter setup", text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=16)).pack(pady=(0, 24))

        ctk.CTkLabel(card, text="Participant ID",
                     font=ctk.CTkFont(size=14)).pack(anchor="w", padx=60)
        self._pid_entry = ctk.CTkEntry(card, width=320, height=40,
                                       placeholder_text="e.g. P01")
        self._pid_entry.pack(padx=60, pady=(4, 20))

        ctk.CTkLabel(card, text="Condition",
                     font=ctk.CTkFont(size=14)).pack(anchor="w", padx=60)
        self._condition_var = ctk.StringVar(value="auto")
        for label, value in [("Auto (random)", "auto"),
                             ("Neutral", config.NEUTRAL),
                             ("Reciprocity", config.RECIPROCITY)]:
            ctk.CTkRadioButton(card, text=label, value=value,
                               variable=self._condition_var).pack(anchor="w", padx=72, pady=3)

        ctk.CTkButton(card, text="Start session", height=46, width=320,
                      font=ctk.CTkFont(size=16, weight="bold"),
                      command=self._start_session).pack(padx=60, pady=(28, 10))

        self._setup_warning = ctk.CTkLabel(card, text="", text_color="#ffb454",
                                           wraplength=360, justify="center",
                                           font=ctk.CTkFont(size=13))
        self._setup_warning.pack(padx=60, pady=(0, 6))

        ctk.CTkButton(card, text="Test robot", width=160, height=36,
                      fg_color=CARD, hover_color=ACCENT, font=ctk.CTkFont(size=13),
                      command=self._test_robot).pack(pady=(0, 10))

        self._robot_status = ctk.CTkLabel(card, text="", text_color=TEXT_DIM,
                                          font=ctk.CTkFont(size=13))
        self._robot_status.pack(padx=60, pady=(0, 28))
        self._poll_robot_status()

    def _poll_robot_status(self):
        """Keep the setup screen's robot-status line up to date."""
        try:
            if self._robot_status.winfo_exists():
                self._robot_status.configure(text=self.robot.status_text())
                self.after(500, self._poll_robot_status)
        except Exception:
            pass

    def _test_robot(self):
        """Make Reachy wave and say hello, to check sound + movement."""
        self.robot.say("Hello! I am ready.", gesture="wave")

    def _start_session(self):
        participant_id = self._pid_entry.get().strip() or "P00"

        # Guard against silently adding a second row for an existing ID: warn
        # once, and only proceed if the user presses Start again with that ID.
        if participant_has_data(config.DATA_DIR, participant_id) and self._dup_pid != participant_id:
            self._dup_pid = participant_id
            self._setup_warning.configure(
                text="⚠  That ID already has saved data. Change it, "
                     "or press Start again to add another row.")
            return

        choice = self._condition_var.get()
        if choice == "auto":                         # keep the two groups close to even
            self.condition = balanced_condition(config.DATA_DIR, config.CONDITIONS)
        else:
            self.condition = choice
        self.logger = ParticipantLogger(config.DATA_DIR, participant_id, self.condition)
        self._q_index = 0
        self.robot.start_idle()          # keep Reachy gently alive for the whole session
        self._show_question()

    # ------------------------------------------------------------------ #
    # 2. A trivia question (read phase, then options)
    # ------------------------------------------------------------------ #
    def _show_question(self):
        self._clear()
        self.robot.stop_tracking()
        self.robot.stop_idle()
        self.robot.look_at(config.GAZE_SCREEN_YAW)   # look toward the laptop while reading
        question = QUESTIONS[self._q_index]
        self._hint_given = False

        # Progress line.
        ctk.CTkLabel(self._container,
                     text=f"Question {self._q_index + 1} of {len(QUESTIONS)}",
                     text_color=TEXT_DIM, font=ctk.CTkFont(size=15)).pack(pady=(28, 0))

        # The question (big and centred during the read phase).
        self._q_label = ctk.CTkLabel(self._container, text=question["text"],
                                     wraplength=820, justify="center",
                                     font=ctk.CTkFont(size=30, weight="bold"))
        self._q_label.pack(pady=(40, 20))

        self._image_label = None
        if question["image"]:
            self._show_image(question["image"])

        # A gentle "get ready" countdown while they read.
        self._countdown = ctk.CTkLabel(self._container, text="",
                                       text_color=TEXT_DIM, font=ctk.CTkFont(size=16))
        self._countdown.pack(pady=10)
        self._tick_read(config.READ_SECONDS)

    def _show_image(self, filename):
        path = config.ASSETS_DIR / filename
        if Image is None or not path.exists():
            ctk.CTkLabel(self._container, text="[image placeholder]",
                         text_color=TEXT_DIM).pack(pady=6)
            return
        pil = Image.open(path)
        max_w, max_h = 360, 230                       # fit within this box, keep aspect
        scale = min(max_w / pil.width, max_h / pil.height)
        size = (int(pil.width * scale), int(pil.height * scale))
        self._image_ref = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
        self._image_label = ctk.CTkLabel(self._container, image=self._image_ref, text="")
        self._image_label.pack(pady=6)

    def _tick_read(self, remaining):
        """Count the read phase down, then reveal the options."""
        if remaining <= 0:
            self._reveal_options()
            return
        self._countdown.configure(text=f"Options appear in {remaining}…")
        self._after(1, lambda: self._tick_read(remaining - 1))

    def _reveal_options(self):
        """Shrink the question to the top and show the four answer buttons."""
        question = QUESTIONS[self._q_index]
        self._countdown.destroy()
        self._q_label.configure(font=ctk.CTkFont(size=20, weight="bold"))

        is_hint = question["hint"] is not None
        options = ctk.CTkFrame(self._container, fg_color="transparent")
        options.pack(pady=24)
        self._option_buttons = []
        for text in question["options"]:
            button = ctk.CTkButton(options, text=text, width=420, height=58,
                                   fg_color=CARD, hover_color=ACCENT,
                                   font=ctk.CTkFont(size=18),
                                   command=lambda choice=text: self._answer(choice))
            button.pack(pady=7)
            if is_hint:
                button.configure(state="disabled")      # locked until the hint is given
            self._option_buttons.append(button)

        # A small status line while a hint is on its way.
        self._hint_status = ctk.CTkLabel(self._container, text="",
                                         text_color=TEXT_DIM, font=ctk.CTkFont(size=14))
        self._hint_status.pack(pady=4)

        if is_hint:
            self.robot.stop_idle()                      # free the worker so the hint is instant
            self._hint_status.configure(
                text="\U0001F4A1  Reachy has a hint for you…",
                text_color=ACCENT, font=ctk.CTkFont(size=16, weight="bold"))
            self._after(config.HINT_DELAY_SECONDS, self._give_hint)
        else:
            self._begin_gaze()                          # turn to the participant (and follow)
            self._q_enabled_at = time.time()

    def _give_hint(self):
        """Announce and speak the scripted hint; unlock the options once it ends."""
        question = QUESTIONS[self._q_index]
        self._hint_given = True
        spoken = HINT_PREFIX + question["hint"]              # say it out loud, every hint
        self.robot.say(spoken, gesture="hint",
                       on_done=lambda: self.after(0, self._enable_options))

    def _enable_options(self):
        """Re-enable the answer buttons after a hint and start the response clock."""
        for button in self._option_buttons:
            try:
                button.configure(state="normal")
            except Exception:
                pass
        self._hint_status.configure(text="")
        self._begin_gaze()                              # now turn to and follow the participant
        self._q_enabled_at = time.time()

    def _begin_gaze(self):
        """Turn to the participant and follow their face (or just hold, if off)."""
        if config.GAZE_TRACKING:
            self.robot.start_tracking()
        else:
            self.robot.look_at(config.GAZE_PARTICIPANT_YAW)

    def _answer(self, choice):
        """Record the answer, show neutral feedback, then move on."""
        self.robot.stop_tracking()
        question = QUESTIONS[self._q_index]
        seconds = time.time() - self._q_enabled_at
        correct = choice == question["answer"]
        self.logger.record_answer(question["id"], choice, correct, seconds, self._hint_given)
        self._show_feedback()

    def _show_feedback(self):
        self._clear()
        card = self._card()
        ctk.CTkLabel(card, text=config.ANSWER_FEEDBACK,
                     font=ctk.CTkFont(size=22)).pack(padx=70, pady=50)
        self.robot.start_idle()
        self._after(config.FEEDBACK_SECONDS, self._next_question)

    def _next_question(self):
        self._q_index += 1
        if self._q_index < len(QUESTIONS):
            self._show_question()
        else:
            self._show_celebration()

    # ------------------------------------------------------------------ #
    # 4. Score, final request and the celebration-button decision
    # ------------------------------------------------------------------ #
    def _show_celebration(self):
        self._clear()
        self.robot.stop_tracking()
        self.robot.stop_idle()           # free the worker so the request is instant

        ctk.CTkLabel(self._container, text="Game over!",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(pady=(60, 6))
        ctk.CTkLabel(self._container,
                     text=f"You scored {self.logger.score} out of {len(QUESTIONS)}",
                     text_color=TEXT_DIM, font=ctk.CTkFont(size=20)).pack(pady=(0, 30))

        # The celebration button is identical in both conditions. It starts
        # disabled and becomes pressable only once Reachy's request has finished,
        # so the 20-second window is measured from the end of the request.
        self._celebrate_btn = ctk.CTkButton(
            self._container, text="\U0001F389  Celebration", width=300, height=70,
            fg_color=CELEBRATE, hover_color="#ff7ba3", state="disabled",
            font=ctk.CTkFont(size=22, weight="bold"),
            command=self._press_celebration)
        self._celebrate_btn.pack(pady=20)

        self._decision_status = ctk.CTkLabel(self._container, text="Reachy is speaking…",
                                             text_color=TEXT_DIM, font=ctk.CTkFont(size=14))
        self._decision_status.pack(pady=6)

        # Revealed below the button once Reachy has finished its request.
        self._leave_label = ctk.CTkLabel(self._container, text="", justify="center",
                                         text_color=TEXT_DIM, font=ctk.CTkFont(size=16))
        self._leave_label.pack(pady=(10, 0))

        # Reachy delivers the condition-specific request; the clock starts after.
        request = config.FINAL_REQUEST[self.condition]
        self.robot.say(request, gesture="request",
                       on_done=lambda: self.after(0, self._open_decision))

    def _open_decision(self):
        """Enable the button, show the goodbye line, start the 20-second window."""
        self._celebrate_btn.configure(state="normal")
        self._decision_status.configure(text="")
        self._leave_label.configure(
            text="Thank you — that's the end of the game.\nYou're free to leave now.")
        self._decision_start = time.time()
        self._after(config.DECISION_SECONDS, self._decision_timeout)

    def _press_celebration(self):
        """Record the press and save; the goodbye line is already on screen."""
        latency = max(0.0, time.time() - self._decision_start)
        self.logger.record_decision(True, latency)
        self.logger.save()
        self._celebrate_btn.configure(state="disabled", text="\U0001F389  Hooray!")
        self.robot.stop_idle()
        if config.CELEBRATION_EMOTION:
            self.robot.play_emotion(config.CELEBRATION_EMOTION)       # built-in dance + music
        else:
            self.robot.say("Woohoo!", gesture=config.CELEBRATION_DANCE)
        self._cancel_timers()

    def _decision_timeout(self):
        """The 20 seconds elapsed with no press: record it and save."""
        if self.logger.pressed is None:
            self.logger.record_decision(False, None)
            self.logger.save()
        self.robot.stop_idle()
