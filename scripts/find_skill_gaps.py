import argparse
import re
from collections import Counter
from typing import List, Set

from pymongo import MongoClient

from scrapers.config import config
from scrapers.skills.extractor import _load_taxonomy

# Generic English stopwords + common job-ad boilerplate that would
# otherwise flood the results without being an actual skill.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "should", "now", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "this", "that", "these", "those", "i", "you", "he", "she", "it",
    "we", "they", "them", "their", "what", "which", "who", "whom",
    "as", "we're", "you'll",
    # job-ad boilerplate that isn't a skill
    "experience", "years", "year", "candidate", "candidates", "role",
    "responsibilities", "responsibility", "requirements", "required",
    "requirement", "preferred", "plus", "must", "including", "team",
    "work", "working", "opportunity", "environment", "knowledge",
    "ability", "strong", "excellent", "good", "skills", "skill",
    "job", "position", "company", "salary", "shift", "office",
    "full-time", "part-time", "on-site", "remote", "internship",
    "intern", "apply", "application", "please", "send", "cv",
    "resume", "looking", "seeking", "join", "growing", "based",
    "based", "well", "etc", "also", "may", "including", "per",
    "month", "monthly", "day", "days", "week", "weekly", "one",
    "two", "three", "new", "using", "use", "used", "including",
    "min", "max", "minimum", "maximum", "least",
    # generic role/action words that show up constantly but aren't skills
    "needed", "know", "understand", "understanding", "manager",
    "management", "junior", "senior", "expert", "operator", "assistant",
    "specialist", "internal", "build", "handling", "fast", "customer",
    "support", "must", "role", "person", "individual", "professional",
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#./-]*")


def tokenize(text: str) -> List[str]:
    """Lowercase and split into word-like tokens, keeping symbol-based
    terms like 'c++', 'c#', 'node.js' intact where possible. Trailing
    punctuation (a period ending a sentence, a stray comma) is
    stripped so 'notion.' doesn't get counted separately from 'notion'."""
    if not text:
        return []
    raw_tokens = TOKEN_PATTERN.findall(text.lower())
    return [t.strip(".") for t in raw_tokens if t.strip(".")]


def extract_candidate_ngrams(text: str, ngram_sizes=(1, 2, 3)) -> Set[str]:
    """
    Build the set of candidate n-grams (word + short phrases) present
    in a single listing's text, with stopwords and pure-numeric tokens
    filtered out.

    Returns a SET (not a list/counter) because we want to count each
    listing at most once per term - document frequency across
    listings, not raw occurrence count within one listing. Otherwise
    one long-winded listing that repeats a word 10 times would drown
    out ten different listings that mention a real skill once each.
    """
    tokens = tokenize(text)
    candidates = set()

    for size in ngram_sizes:
        for i in range(len(tokens) - size + 1):
            gram_tokens = tokens[i:i + size]

            # Skip if any token in the phrase is a stopword/number -
            # avoids junk like "the react" or "experience with"
            if any(
                tok in STOPWORDS or tok.isdigit() or len(tok) < 2
                for tok in gram_tokens
            ):
                continue

            candidates.add(" ".join(gram_tokens))

    return candidates


def find_skill_gaps(top_n: int = 50, min_count: int = 5) -> List[tuple]:
    """
    Scan all listings and return the top_n most common n-grams that
    appear in at least min_count distinct listings and aren't already
    in the taxonomy.

    Returns:
        List of (term, listing_count) tuples, sorted by count descending.
    """
    known_skills = set(_load_taxonomy())

    client = MongoClient(config.MONGO_URI)
    db = client[config.DATABASE_NAME]

    doc_frequency = Counter()

    for doc in db.listings.find({}, {"title": 1, "description_raw": 1}):
        text = f"{doc.get('title', '')} {doc.get('description_raw', '')}"
        candidates = extract_candidate_ngrams(text)
        # Only count terms not already covered by the taxonomy
        new_candidates = candidates - known_skills
        doc_frequency.update(new_candidates)

    client.close()

    ranked = [
        (term, count)
        for term, count in doc_frequency.most_common()
        if count >= min_count
    ]
    return ranked[:top_n]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find recurring skill gaps in taxonomy.json")
    parser.add_argument("--top", type=int, default=50, help="Max number of terms to show")
    parser.add_argument("--min-count", type=int, default=5,
                         help="Minimum number of distinct listings a term must appear in")
    args = parser.parse_args()

    print(f"Scanning listings for terms appearing in {args.min_count}+ listings, "
          f"not already in taxonomy.json...\n")

    results = find_skill_gaps(top_n=args.top, min_count=args.min_count)

    if not results:
        print("No gaps found above the threshold - try lowering --min-count.")
    else:
        print(f"{'TERM':<35} {'LISTINGS'}")
        print("-" * 45)
        for term, count in results:
            print(f"{term:<35} {count}")