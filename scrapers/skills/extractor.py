"""
SkillSync - Rule-Based Skill Extraction (Phase 2, non-ML)

Extracts skills from listing text by matching against a curated taxonomy
(taxonomy.json). This is deliberately NOT an NLP/ML approach - no spaCy,
no trained model, no probabilistic tagging. It's deterministic keyword
matching, which is:
  - Easy to explain and defend (every match traces back to a taxonomy entry)
  - Fast (no model loading, no GPU/inference cost)
  - Easy to extend (just add a term to taxonomy.json)

Trade-off: it will miss skills phrased in ways not in the taxonomy, and
it can't infer skills that are implied but never named. That's an
accepted limitation for Phase 2 - the taxonomy is meant to grow over
time as you see more listings.
"""

import json
import re
from pathlib import Path
from functools import lru_cache
from typing import List

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"


@lru_cache(maxsize=1)
def _load_taxonomy() -> List[str]:
    """
    Load and flatten taxonomy.json into a single list of skill strings,
    sorted longest-first (by word count, then character length).

    Longest-first matters: "react native" should be checked before
    "react" so a listing mentioning React Native gets tagged with the
    more specific skill, not just the generic one. (We still return
    both if both appear - see extract_skills - this just controls
    match order, not exclusivity.)
    """
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)

    all_skills = set()
    for skill_list in categories.values():
        for skill in skill_list:
            all_skills.add(skill.lower().strip())

    return sorted(all_skills, key=lambda s: (-len(s.split()), -len(s)))


def _build_pattern(skill: str) -> re.Pattern:
    """
    Build a boundary-aware regex for a skill term.

    Uses lookaround instead of \\b because \\b doesn't behave well
    around symbols like '+', '#', '.' (e.g. "c++", "c#", "node.js") -
    \\b only cares about \\w vs non-\\w transitions, which misfires on
    those. This checks "not preceded/followed by a word character"
    instead, which works for both plain words and symbol-containing terms.
    """
    escaped = re.escape(skill)
    # Allow an optional trailing 's' so plurals match (e.g. "rest apis"
    # matches the taxonomy entry "rest api"). Only applied when the skill
    # ends in a letter/digit - terms like "c++" or "c#" skip this since
    # pluralizing a symbol doesn't make sense.
    plural_suffix = "s?" if skill[-1].isalnum() else ""
    # Boundary class includes + and # in addition to \w. Without this,
    # "c" would falsely match inside "c#" or "c++", since \b/\w only
    # treats letters/digits/underscore as "word" characters - '#' and '+'
    # look like a boundary to \w even though they're part of the term.
    boundary = r"[\w+#]"
    return re.compile(
        rf"(?<!{boundary}){escaped}{plural_suffix}(?!{boundary})", re.IGNORECASE
    )


@lru_cache(maxsize=None)
def _compiled_patterns():
    return [(skill, _build_pattern(skill)) for skill in _load_taxonomy()]


def extract_skills(text: str) -> List[str]:
    """
    Extract taxonomy skills mentioned in the given text.

    Args:
        text: Raw text to scan (typically description_raw + title).

    Returns:
        Sorted list of matched skill strings (deduplicated). Empty list
        if text is empty or no skills matched.

    Example:
        >>> extract_skills("Looking for a React Native dev, Firebase and Git experience a plus")
        ['firebase', 'git', 'react', 'react native']
    """
    if not text:
        return []

    matched = set()
    for skill, pattern in _compiled_patterns():
        if pattern.search(text):
            matched.add(skill)

    return sorted(matched)


def reload_taxonomy():
    """
    Clear cached taxonomy/patterns so a taxonomy.json edit takes effect
    without restarting the process. Call this after updating the file
    in a long-running service (e.g. from an admin endpoint), otherwise
    just restarting the scraper picks it up automatically.
    """
    _load_taxonomy.cache_clear()
    _compiled_patterns.cache_clear()


if __name__ == "__main__":
    # Quick manual smoke test
    sample = (
        "We are hiring a Frontend Developer with experience in React, "
        "Next.js, and Tailwind CSS. Familiarity with REST APIs, Git, "
        "and basic UI/UX principles is a plus. Strong communication "
        "and teamwork skills required."
    )
    print(extract_skills(sample))
