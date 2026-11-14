"""The six trivia questions, kept as plain data so they are easy to swap.

Each question is a dict:
    id       - short unique key I use in the data files
    text     - the question shown on screen
    image    - a filename inside assets/, or None for a text-only question
    options  - the four answer choices, shown in THIS fixed order (same for
               every participant, for consistency)
    answer   - the correct option (must match one of the options exactly)
    hint     - Reachy's spoken hint, or None if this question has no hint

The study needs exactly three hint questions out of six, and the hints are
spoken by Reachy (not shown on screen). Here the hint questions are the flag,
the planet and the script.
"""
from __future__ import annotations

QUESTIONS = [
    {
        "id": "nobel",
        "text": "Who was the first person to win Nobel Prizes in two different "
                "scientific fields?",
        "image": None,
        "options": ["Marie Curie", "Linus Pauling", "Albert Einstein", "Niels Bohr"],
        "answer": "Marie Curie",
        "hint": None,
    },
    {
        "id": "flag",
        "text": "Which country's flag is this?",
        "image": "flag_equatorial_guinea.png",
        "options": ["Equatorial Guinea", "Gabon", "Guinea", "Cameroon"],
        "answer": "Equatorial Guinea",
        "hint": "This is the only country in Africa where Spanish is an official language.",
    },
    {
        "id": "crest",
        "text": "Which football club's crest is this?",
        "image": "crest_fiorentina.png",
        "options": ["Fiorentina", "AS Roma", "Torino", "Lazio"],
        "answer": "Fiorentina",
        "hint": None,
    },
    {
        "id": "planet",
        "text": "Which planet in our solar system has the shortest day?",
        "image": None,
        "options": ["Jupiter", "Mercury", "Earth", "Saturn"],
        "answer": "Jupiter",
        "hint": "The fastest-spinning planet is a gas giant, not the smallest planet.",
    },
    {
        "id": "script",
        "text": "Which language is written in this script?",
        "image": "script_javanese.png",
        "options": ["Javanese", "Thai", "Khmer", "Burmese"],
        "answer": "Javanese",
        "hint": "This script comes from the world's most populous island.",
    },
    {
        "id": "grammy",
        "text": "Which artist has won the most Grammy Awards of all time?",
        "image": None,
        "options": ["Beyonce", "Quincy Jones", "Georg Solti", "Taylor Swift"],
        "answer": "Beyonce",
        "hint": None,
    },
]
