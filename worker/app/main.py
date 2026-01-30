import asyncio
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from shared.core import database, models
from worker.app.scraper import ScraperEngine
from worker.app.logger import remote_logger
from sqlalchemy import select
import json
import asyncpg
from shared.core.database import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

scheduler = AsyncIOScheduler()
scraper = ScraperEngine()
current_interval = 600

async def get_scrape_interval():
    try:
        async with database.AsyncSessionLocal() as db:
            result = await db.execute(select(models.Setting).where(models.Setting.key == "scrape_interval_minutes"))
            setting = result.scalar_one_or_none()
            if setting:
                return int(setting.value) * 60
    except Exception as e:
        logger.error(f"Error fetching scrape interval: {e}")
    return 600  # Default 10 minutes

def update_scheduler(interval):
    global current_interval
    if interval != current_interval:
        logger.info(f"Updating scrape interval to {interval} seconds")
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.id == 'scrape_job':
                job.modify(trigger='interval', seconds=interval)
        current_interval = interval

async def process_site(db, site):
    try:
        logger.info(f"Processing site: {site.name}")
        await remote_logger.log(f"Processing site: {site.name}", level="info", extra={"site_id": site.id})
        
        # Create Run
        run = models.ScrapeRun(site_id=site.id)
        db.add(run)
        await db.commit()
        await db.refresh(run)
        
        # Discovery
        await scraper.run_discovery_phase(db, site, run.id)
        
        # Processing
        pages_per_run = int(os.getenv("PAGES_PER_RUN", 200))
        await scraper.run_processing_phase(db, site, run.id, limit=pages_per_run)
        
    except Exception as e:
        logger.error(f"Error processing site {site.name}: {e}")
        await remote_logger.log(f"Error processing site {site.name}: {e}", level="error", extra={"site_id": site.id})

async def scrape_job():
    logger.info("Starting scheduled scrape job...")
    await remote_logger.log("Starting scheduled scrape job...", level="info")
    
    async with database.AsyncSessionLocal() as db:
        # Get enabled sites
        result = await db.execute(select(models.Site).where(models.Site.enabled == True))
        sites = result.scalars().all()
        
        if not sites:
            await remote_logger.log("No enabled sites found.", level="warning")
            return

        for site in sites:
            await process_site(db, site)

    await remote_logger.log("Scheduled scrape job finished.", level="info")

async def run_manual_scrape(site_id: str):
    logger.info(f"Starting manual scrape for site {site_id}...")
    await remote_logger.log(f"Manual scrape triggered for site {site_id}", level="info")
    
    async with database.AsyncSessionLocal() as db:
        result = await db.execute(select(models.Site).where(models.Site.id == site_id))
        site = result.scalar_one_or_none()
        
        if not site:
            await remote_logger.log(f"Site {site_id} not found for manual run.", level="error")
            return
            
        await process_site(db, site)
    
    await remote_logger.log(f"Manual scrape finished for site {site.name}", level="info")

async def listen_for_commands():
    # asyncpg expects 'postgresql://' not 'postgresql+asyncpg://'
    dsn = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(dsn)
        
        async def handle_command(connection, pid, channel, payload):
            try:
                data = json.loads(payload)
                if data.get("command") == "scrape":
                    site_id = data.get("site_id")
                    if site_id:
                        asyncio.create_task(run_manual_scrape(site_id))
                elif data.get("command") == "reload_settings":
                    interval = await get_scrape_interval()
                    update_scheduler(interval)
            except Exception as e:
                logger.error(f"Error handling command: {e}")

        await conn.add_listener("worker_commands", handle_command)
        logger.info("Listening for worker commands on 'worker_commands' channel...")
        
        while True:
            await asyncio.sleep(60)
            if conn.is_closed():
                break
    except Exception as e:
        logger.error(f"Connection error in command listener: {e}")
        await asyncio.sleep(5)
        # Recursive restart on failure
        asyncio.create_task(listen_for_commands())

async def main():
    logger.info("Worker initializing...")
    await remote_logger.initialize()
    
    # Add job
    interval = await get_scrape_interval()
    global current_interval
    current_interval = interval
    scheduler.add_job(scrape_job, 'interval', seconds=interval, id='scrape_job')
    
    scheduler.start()
    
    # Run once immediately
    asyncio.create_task(scrape_job())
    
    # Start command listener
    asyncio.create_task(listen_for_commands())
    
    try:
        # Keep alive
        while True:
            await asyncio.sleep(10)
    except (KeyboardInterrupt, asyncio.CancelledError):
        scheduler.shutdown()
        await scraper.close()
        await remote_logger.close()

if __name__ == "__main__":
    asyncio.run(main())
