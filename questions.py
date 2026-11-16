"""The ten trivia questions, kept as plain data so they are easy to swap.

Each question is a dict:
    id       - short unique key I use in the data files
    text     - the question shown on screen
    image    - a filename inside assets/, or None for a text-only question
    options  - the four answer choices, shown in THIS fixed order (same for
               every participant, for consistency)
    answer   - the correct option (must match one of the options exactly)
    hint     - Reachy's spoken hint (every question has one; it is spoken, not
               shown on screen)

The new design uses ten questions and Reachy gives a hint on every one. Three of
them (the flag, the crest and the script) show an image from assets/; the rest
are text only. The questions are drawn from our group question bank, chosen so
each has a hint that helps without giving the answer away.
"""
from __future__ import annotations

QUESTIONS = [
    {
        "id": "flag",
        "text": "Which country's flag is this?",
        "image": "flag_equatorial_guinea.png",
        "options": ["Equatorial Guinea", "Gabon", "Guinea", "Cameroon"],
        "answer": "Equatorial Guinea",
        "hint": "This is the only country in Africa where Spanish is an official language.",
    },
    {
        "id": "planet",
        "text": "Which planet in our solar system has the shortest day?",
        "image": None,
        "options": ["Jupiter", "Mercury", "Earth", "Saturn"],
        "answer": "Jupiter",
        "hint": "The fastest-spinning planet is a gas giant, and it is not the smallest planet.",
    },
    {
        "id": "timezones",
        "text": "Which country spans the most time zones?",
        "image": None,
        "options": ["France", "Russia", "USA", "UK"],
        "answer": "France",
        "hint": "Its overseas territories are scattered across every ocean.",
    },
    {
        "id": "crest",
        "text": "Which football club's crest is this?",
        "image": "crest_fiorentina.png",
        "options": ["Fiorentina", "AS Roma", "Torino", "Lazio"],
        "answer": "Fiorentina",
        "hint": "This Italian club is nicknamed La Viola, after the purple it plays in.",
    },
    {
        "id": "element",
        "text": "Which chemical element has the symbol W?",
        "image": None,
        "options": ["Tungsten", "Tin", "Titanium", "Zinc"],
        "answer": "Tungsten",
        "hint": "Its symbol comes from its German name, and it was used in old light-bulb filaments.",
    },
    {
        "id": "pyramids",
        "text": "Which country has the most pyramids?",
        "image": None,
        "options": ["Sudan", "Egypt", "Mexico", "Peru"],
        "answer": "Sudan",
        "hint": "It's not Egypt, but it is Egypt's southern neighbour.",
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
        "id": "scotland",
        "text": "What is the national animal of Scotland?",
        "image": None,
        "options": ["Unicorn", "Red deer", "Golden eagle", "Highland cow"],
        "answer": "Unicorn",
        "hint": "It appears on the royal coat of arms alongside a lion.",
    },
    {
        "id": "octopus",
        "text": "Which animal has three hearts?",
        "image": None,
        "options": ["Octopus", "Jellyfish", "Starfish", "Seahorse"],
        "answer": "Octopus",
        "hint": "It's a soft-bodied sea creature that can change colour and squirt ink.",
    },
    {
        "id": "petra",
        "text": "In which country is the ancient city of Petra?",
        "image": None,
        "options": ["Jordan", "Egypt", "Syria", "Lebanon"],
        "answer": "Jordan",
        "hint": "This kingdom lies between Israel and Saudi Arabia, touching both the Dead Sea and the Red Sea.",
    },
]
