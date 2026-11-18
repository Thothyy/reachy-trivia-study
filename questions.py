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

The design uses ten questions and Reachy gives a hint on every one. Two of them
(the script and the crest) show an image from assets/; the rest are text only.
The questions are drawn from our group question bank, chosen so each has a hint
that helps without giving the answer away.
"""
from __future__ import annotations

QUESTIONS = [
    {
        "id": "nobel",
        "text": "Who was the first person to win Nobel Prizes in two different scientific fields?",
        "image": None,
        "options": ["Marie Curie", "Linus Pauling", "Albert Einstein", "Niels Bohr"],
        "answer": "Marie Curie",
        "hint": "She discovered two new elements, and named one of them after her home country.",
    },
    {
        "id": "grammy",
        "text": "Which artist has won the most Grammy Awards of all time?",
        "image": None,
        "options": ["Beyoncé", "Quincy Jones", "Georg Solti", "Taylor Swift"],
        "answer": "Beyoncé",
        "hint": "In 2023 she overtook the classical conductor who had held the record for decades. Her husband is a Grammy-winning rapper.",
    },
    {
        "id": "timezones",
        "text": "Which country spans the most time zones?",
        "image": None,
        "options": ["France", "Russia", "USA", "UK"],
        "answer": "France",
        "hint": "Its overseas territories are scattered across every ocean, from the Pacific to the Indian Ocean.",
    },
    {
        "id": "pyramids",
        "text": "Which country has the most pyramids?",
        "image": None,
        "options": ["Sudan", "Egypt", "Mexico", "Peru"],
        "answer": "Sudan",
        "hint": "Surprisingly, it isn't Egypt. The ancient Kingdom of Kush built over 200 smaller pyramids further up the Nile.",
    },
    {
        "id": "element",
        "text": "Which chemical element has the symbol W?",
        "image": None,
        "options": ["Tungsten", "Tin", "Titanium", "Zinc"],
        "answer": "Tungsten",
        "hint": "It's the metal that glowed inside old light-bulb filaments. The W comes from its German name.",
    },
    {
        "id": "script",
        "text": "Which language is written in this script?",
        "image": "script_javanese.png",
        "options": ["Javanese", "Thai", "Khmer", "Burmese"],
        "answer": "Javanese",
        "hint": "This script comes from an island that shares its name with a programming language and a type of coffee.",
    },
    {
        "id": "islands",
        "text": "Which country has the most islands?",
        "image": None,
        "options": ["Sweden", "Indonesia", "Philippines", "Canada"],
        "answer": "Sweden",
        "hint": "Forget the tropics. Think of a cold Nordic coastline broken into more than 200,000 tiny islands.",
    },
    {
        "id": "scotland",
        "text": "What is the national animal of Scotland?",
        "image": None,
        "options": ["Unicorn", "Red deer", "Golden eagle", "Highland cow"],
        "answer": "Unicorn",
        "hint": "It doesn't exist. Look at the UK royal coat of arms: it's the one standing opposite the lion.",
    },
    {
        "id": "berry",
        "text": "Which of these fruits is botanically a berry?",
        "image": None,
        "options": ["Banana", "Strawberry", "Raspberry", "Cherry"],
        "answer": "Banana",
        "hint": "The fruits with 'berry' in their names are the impostors.",
    },
    {
        "id": "crest",
        "text": "Which football club's badge is this?",
        "image": "crest_fiorentina.png",
        "options": ["Fiorentina", "Parma", "Torino", "Sampdoria"],
        "answer": "Fiorentina",
        "hint": "The lily on the badge is the symbol of the city where the Renaissance began.",
    },
]
