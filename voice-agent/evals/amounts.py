from __future__ import annotations

import re


_SMALL = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_NUMBER_WORDS = set(_SMALL) | {"hundred", "thousand", "and"}
_RATE_CONTEXT = {"rate", "offer", "offered", "do", "at", "for", "maximum", "budget", "price", "dollars", "bucks"}


def _words_to_int(words: list[str]) -> int | None:
    total = current = 0
    saw_number = False
    for word in words:
        if word == "and":
            continue
        if word in _SMALL:
            current += _SMALL[word]
            saw_number = True
        elif word == "hundred" and current:
            current *= 100
        elif word == "thousand" and current:
            total += current * 1000
            current = 0
        else:
            return None
    value = total + current
    return value if saw_number and value >= 100 else None


def extract_rate_amounts(text: str) -> list[int]:
    """Extract currency-like amounts without treating IDs, dates, or phones as rates."""
    lowered = text.lower().replace(",", "")
    found: list[tuple[int, int]] = []
    numeric_patterns = (
        r"\$\s*(\d{3,5})(?:\.\d{1,2})?",
        r"\busd\s*(\d{3,5})(?:\.\d{1,2})?\b",
        r"\b(\d{3,5})(?:\.\d{1,2})?\s*(?:dollars?|bucks?)\b",
    )
    for pattern in numeric_patterns:
        for match in re.finditer(pattern, lowered):
            found.append((match.start(), int(match.group(1))))

    tokens = list(re.finditer(r"[a-z]+", lowered))
    index = 0
    while index < len(tokens):
        if tokens[index].group() not in _NUMBER_WORDS:
            index += 1
            continue
        end = index
        while end < len(tokens) and tokens[end].group() in _NUMBER_WORDS:
            end += 1
        words = [token.group() for token in tokens[index:end]]
        value = _words_to_int(words)
        nearby = {token.group() for token in tokens[max(0, index - 3):min(len(tokens), end + 3)]}
        if value is not None and nearby & _RATE_CONTEXT:
            found.append((tokens[index].start(), value))
        index = end

    return [value for _position, value in sorted(set(found))]
