"""
Unit tests for scrapers.skills.extractor

Run with: pytest tests/test_skill_extractor.py -v
"""

import pytest
from scrapers.skills.extractor import extract_skills


def test_basic_multi_skill_match():
    text = "Looking for a Frontend Developer with React and Tailwind CSS experience."
    result = extract_skills(text)
    assert "react" in result
    assert "tailwind css" in result


def test_case_insensitive():
    assert "python" in extract_skills("Strong PYTHON and sql background required")
    assert "sql" in extract_skills("Strong PYTHON and sql background required")


def test_longer_phrase_preferred_alongside_shorter():
    # Both "react" and "react native" should be returned - extraction
    # isn't exclusive, it just tags every taxonomy term that appears.
    result = extract_skills("React Native experience required")
    assert "react" in result
    assert "react native" in result


def test_symbol_skills_no_false_positive():
    # "c" must not match inside "c++" or "c#"
    result = extract_skills("Experience with C++ or C# preferred")
    assert "c++" in result
    assert "c#" in result
    assert "c" not in result


def test_symbol_skills_standalone_still_matches():
    result = extract_skills("Basic C programming knowledge")
    assert "c" in result


def test_plural_handling():
    result = extract_skills("Must be comfortable building REST APIs")
    assert "rest api" in result


def test_empty_text_returns_empty_list():
    assert extract_skills("") == []
    assert extract_skills(None) == []


def test_no_matching_skills():
    result = extract_skills("This text has nothing relevant in our taxonomy at all")
    assert result == []


def test_no_duplicate_entries():
    result = extract_skills("Python python PYTHON everywhere, Python is great")
    assert result.count("python") == 1


def test_result_is_sorted():
    result = extract_skills("React, Python, Git, AWS all required")
    assert result == sorted(result)
