"""
SkillSync - Backfill skills on existing listings

One-time (or re-runnable) maintenance script. The skill extractor only
runs on listings as they pass through pipeline.py, so anything already
sitting in MongoDB from before you wired it in has skills=[]. This
script re-scans those listings' existing text and fills skills in
without needing to re-scrape.

Safe to run more than once - it only touches listings where
skills is currently empty, so already-backfilled or freshly-scraped
listings (which already have skills from the pipeline) are skipped.

Usage:
    python -m scripts.backfill_skills
    (run from the repo root, with your venv active and MongoDB running)
"""

from pymongo import MongoClient

from scrapers.config import config
from scrapers.skills.extractor import extract_skills


def backfill_skills() -> dict:
    client = MongoClient(config.MONGO_URI)
    db = client[config.DATABASE_NAME]
    listings = db[config.LISTINGS_COLLECTION]

    stats = {"scanned": 0, "updated": 0, "skipped_no_match": 0}

    cursor = listings.find({"skills": []})
    for doc in cursor:
        stats["scanned"] += 1
        text = f"{doc.get('title', '')} {doc.get('description_raw', '')}"
        skills = extract_skills(text)

        if skills:
            listings.update_one({"_id": doc["_id"]}, {"$set": {"skills": skills}})
            stats["updated"] += 1
        else:
            stats["skipped_no_match"] += 1

    client.close()
    return stats


if __name__ == "__main__":
    print("Backfilling skills on existing listings...")
    result = backfill_skills()
    print(
        f"Done. Scanned {result['scanned']} listings, "
        f"updated {result['updated']}, "
        f"{result['skipped_no_match']} had no matching skills."
    )