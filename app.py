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

import random
import time

import customtkinter as ctk

import config
from logger import ParticipantLogger
from questions import QUESTIONS

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
                      command=self._start_session).pack(padx=60, pady=(28, 40))

    def _start_session(self):
        participant_id = self._pid_entry.get().strip() or "P00"
        choice = self._condition_var.get()
        self.condition = random.choice(config.CONDITIONS) if choice == "auto" else choice
        self.logger = ParticipantLogger(config.DATA_DIR, participant_id, self.condition)
        self._q_index = 0
        self._show_briefing()

    # ------------------------------------------------------------------ #
    # 2. Briefing + comprehension check
    # ------------------------------------------------------------------ #
    def _show_briefing(self):
        self._clear()
        card = self._card()

        ctk.CTkLabel(card, text="Before we start",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(padx=50, pady=(36, 16))
        ctk.CTkLabel(card, text=config.BRIEFING_TEXT, justify="left", wraplength=620,
                     font=ctk.CTkFont(size=16)).pack(padx=50, pady=(0, 24))

        self._understood = ctk.BooleanVar(value=False)
        begin = ctk.CTkButton(card, text="Begin the game", height=46, width=320,
                              state="disabled",
                              font=ctk.CTkFont(size=16, weight="bold"),
                              command=self._begin_quiz)

        def toggle():
            begin.configure(state="normal" if self._understood.get() else "disabled")

        ctk.CTkCheckBox(card, text=config.COMPREHENSION_PROMPT,
                        variable=self._understood, command=toggle,
                        font=ctk.CTkFont(size=15)).pack(padx=50, pady=(0, 24))
        begin.pack(padx=50, pady=(0, 36))

    def _begin_quiz(self):
        self._q_index = 0
        self._show_question()

    # ------------------------------------------------------------------ #
    # 3. A trivia question (read phase, then options)
    # ------------------------------------------------------------------ #
    def _show_question(self):
        self._clear()
        self.robot.stop_idle()
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
        self._image_ref = ctk.CTkImage(light_image=pil, dark_image=pil, size=(260, 170))
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

        options = ctk.CTkFrame(self._container, fg_color="transparent")
        options.pack(pady=24)
        for text in question["options"]:
            ctk.CTkButton(options, text=text, width=420, height=58,
                          fg_color=CARD, hover_color=ACCENT,
                          font=ctk.CTkFont(size=18),
                          command=lambda choice=text: self._answer(choice)).pack(pady=7)

        self._q_enabled_at = time.time()
        # On a hint question, Reachy offers its scripted hint a moment later.
        if question["hint"]:
            self._after(config.HINT_DELAY_SECONDS, self._give_hint)

    def _give_hint(self):
        question = QUESTIONS[self._q_index]
        self._hint_given = True
        self.robot.say(question["hint"], gesture="hint")

    def _answer(self, choice):
        """Record the answer, show neutral feedback, then move on."""
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
        self.robot.stop_idle()

        ctk.CTkLabel(self._container, text="Game over!",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(pady=(60, 6))
        ctk.CTkLabel(self._container,
                     text=f"You scored {self.logger.score} out of {len(QUESTIONS)}",
                     text_color=TEXT_DIM, font=ctk.CTkFont(size=20)).pack(pady=(0, 30))

        # The celebration button is identical in both conditions.
        self._celebrate_btn = ctk.CTkButton(
            self._container, text="\U0001F389  Celebration", width=300, height=70,
            fg_color=CELEBRATE, hover_color="#ff7ba3",
            font=ctk.CTkFont(size=22, weight="bold"),
            command=self._press_celebration)
        self._celebrate_btn.pack(pady=20)

        self._decision_status = ctk.CTkLabel(self._container, text="",
                                             text_color=TEXT_DIM,
                                             font=ctk.CTkFont(size=14))
        self._decision_status.pack(pady=6)

        # Reachy delivers the condition-specific request, then the clock starts.
        request = config.FINAL_REQUEST[self.condition]
        self.robot.say(request, gesture="request")
        est = max(3.0, len(request.split()) / 2.5)   # rough spoken length in seconds
        self._decision_start = time.time() + est
        self._after(est + config.DECISION_SECONDS, self._decision_timeout)

    def _press_celebration(self):
        latency = max(0.0, time.time() - self._decision_start)
        self.logger.record_decision(True, latency)
        self._celebrate_btn.configure(state="disabled", text="\U0001F389  Hooray!")
        self._decision_status.configure(text="Thanks! Continuing…")
        self.robot.gesture("nod")
        self._cancel_timers()
        self._after(1.6, self._show_manipulation)

    def _decision_timeout(self):
        if self.logger.pressed is None:              # they chose not to press
            self.logger.record_decision(False, None)
        self._show_manipulation()

    # ------------------------------------------------------------------ #
    # 5. Manipulation check, then the end
    # ------------------------------------------------------------------ #
    def _show_manipulation(self):
        self._clear()
        card = self._card()
        ctk.CTkLabel(card, text=config.MANIPULATION_QUESTION, wraplength=560,
                     justify="center",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(padx=60, pady=(40, 24))
        for option in config.MANIPULATION_OPTIONS:
            ctk.CTkButton(card, text=option, width=300, height=50,
                          fg_color=CARD, hover_color=ACCENT,
                          font=ctk.CTkFont(size=17),
                          command=lambda value=option: self._answer_manipulation(value)
                          ).pack(pady=7, padx=60)
        ctk.CTkLabel(card, text="", height=10).pack()

    def _answer_manipulation(self, value):
        self.logger.record_manipulation(value)
        self.logger.save()
        self._show_end()

    def _show_end(self):
        self._clear()
        card = self._card()
        ctk.CTkLabel(card, text="Thank you!",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(padx=70, pady=(46, 10))
        ctk.CTkLabel(card,
                     text="Please complete the short questionnaire to finish.\n"
                          f"{config.QUESTIONNAIRE_URL}",
                     justify="center", text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=16)).pack(padx=70, pady=(0, 24))
        ctk.CTkButton(card, text="Close", width=240, height=44,
                      command=self._on_close).pack(pady=(0, 44))
