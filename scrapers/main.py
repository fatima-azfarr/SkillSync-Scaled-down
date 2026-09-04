"""
SkillSync - Scraper Service Entry Point

This is the main file that runs all 6 scrapers. It:
1. Connects to MongoDB
2. Creates all 6 scraper instances
3. Runs all scrapers once on startup
4. Sets up APScheduler to re-run them every 12 hours

APScheduler (Advanced Python Scheduler) is a library that lets us
schedule tasks to run at specific intervals — like a cron job but
inside our Python application.

Usage:
    python -m scrapers.main
    
Or via Docker:
    docker-compose up scrapers
"""

import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from scrapers.pipeline import Pipeline
from scrapers.logger import get_logger
from scrapers.config import config

# Import all 6 scrapers
from scrapers.spiders.rozee import RozeeScraper
from scrapers.spiders.mustakbil import MustakbilScraper
from scrapers.spiders.internee import InterneeScraper
from scrapers.spiders.remotive import RemotiveScraper
from scrapers.spiders.devpost import DevpostScraper
from scrapers.spiders.wuzzuf import WuzzufScraper

logger = get_logger("main")


def run_all_scrapers():
    """
    Run all 6 scrapers and process their results through the pipeline.
    
    Each scraper runs independently — if one fails, the others continue.
    This is achieved by each scraper's run() method catching all exceptions
    and returning an empty list on failure.
    """
    logger.info("=" * 60)
    logger.info("STARTING SCRAPE CYCLE")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    logger.info("=" * 60)
    
    # Create all 6 scrapers
    scrapers = [
        MustakbilScraper(),    # Static (BeautifulSoup)
        WuzzufScraper(),       # Static (BeautifulSoup)
        RemotiveScraper(),     # JSON API (simplest)
        RozeeScraper(),        # Dynamic (Selenium)
        InterneeScraper(),     # Dynamic (Selenium)
        DevpostScraper(),      # Dynamic (Selenium)
    ]
    
    # Connect to MongoDB
    pipeline = Pipeline()
    pipeline.connect()
    
    # Track overall statistics
    total_stats = {"found": 0, "new": 0, "failed": 0}
    
    try:
        for scraper in scrapers:
            logger.info(f"\nRunning scraper: {scraper.name}")
            
            # run() catches all exceptions internally and returns [] on failure
            raw_listings = scraper.run()
            
            if raw_listings:
                # Process through the pipeline: clean → fingerprint → dedupe → save
                stats = pipeline.process_listings(raw_listings, scraper.name)
                total_stats["found"] += stats["found"]
                total_stats["new"] += stats["new"]
                total_stats["failed"] += stats["failed"]
            else:
                logger.warning(f"Scraper '{scraper.name}' returned no listings")
    
    finally:
        pipeline.close()
    
    # Log overall summary
    logger.info("=" * 60)
    logger.info("SCRAPE CYCLE COMPLETE")
    logger.info(f"  Total listings found: {total_stats['found']}")
    logger.info(f"  Total new listings: {total_stats['new']}")
    logger.info(f"  Total failed: {total_stats['failed']}")
    logger.info("=" * 60)


def main():
    """
    Main entry point for the scraper service.
    
    1. Runs all scrapers immediately on startup
    2. Then schedules them to run every 12 hours via APScheduler
    """
    logger.info("SkillSync Scraper Service Starting...")
    logger.info(f"MongoDB URI: {config.MONGO_URI}")
    logger.info(f"Scrape interval: {config.SCRAPE_INTERVAL_HOURS} hours")
    
    # Run scrapers once immediately on startup
    logger.info("Running initial scrape cycle...")
    run_all_scrapers()
    
    # Set up APScheduler to run scrapers every 12 hours
    # BlockingScheduler keeps the process alive while waiting for the next run
    scheduler = BlockingScheduler()
    
    scheduler.add_job(
        run_all_scrapers,
        trigger="interval",
        hours=config.SCRAPE_INTERVAL_HOURS,
        id="scrape_all",
        name="Run all 6 scrapers",
        next_run_time=None,  # Don't run again immediately (we just ran above)
    )
    
    logger.info(f"Scheduler started. Next scrape in {config.SCRAPE_INTERVAL_HOURS} hours.")
    logger.info("Press Ctrl+C to stop.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")


if __name__ == "__main__":
    main()
