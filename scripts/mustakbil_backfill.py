from pymongo import MongoClient

from scrapers.config import config
from scrapers.skills.extractor import extract_skills
from scrapers.spiders.mustakbil import MustakbilScraper


def backfill_mustakbil_descriptions() -> dict:
    client = MongoClient(config.MONGO_URI)
    db = client[config.DATABASE_NAME]
    listings = db[config.LISTINGS_COLLECTION]

    stale = list(listings.find({"source": "mustakbil", "description_raw": ""}))
    stats = {"stale_found": len(stale), "updated": 0, "no_longer_live": 0}

    if not stale:
        client.close()
        return stats

    print(f"Found {len(stale)} stale mustakbil listings. Fetching fresh data...")
    scraper = MustakbilScraper()
    fresh_listings = scraper.run()
    fresh_by_url = {item["source_url"]: item for item in fresh_listings}

    for doc in stale:
        fresh = fresh_by_url.get(doc["source_url"])
        if not fresh:
            stats["no_longer_live"] += 1
            continue

        skills = extract_skills(f"{fresh['title']} {fresh['description_raw']}")
        listings.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "description_raw": fresh["description_raw"],
                    "location": fresh["location"],
                    "posted_date": fresh["posted_date"],
                    "deadline": fresh["deadline"],
                    "skills": skills,
                }
            },
        )
        stats["updated"] += 1

    client.close()
    return stats


if __name__ == "__main__":
    print("Backfilling descriptions for stale mustakbil listings...")
    result = backfill_mustakbil_descriptions()
    print(
        f"Done. {result['stale_found']} stale listings found, "
        f"{result['updated']} updated, "
        f"{result['no_longer_live']} no longer appear in the API "
        f"(likely expired/removed postings)."
    )