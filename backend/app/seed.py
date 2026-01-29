import asyncio
from sqlalchemy import select
from shared.core import database, models

async def seed():
    async with database.AsyncSessionLocal() as db:
        print("Seeding data...")
        
        # Check if sites exist
        result = await db.execute(select(models.Site))
        existing_sites = result.scalars().all()
        existing_urls = {s.base_url for s in existing_sites}
        
        sites_to_create = [
            models.Site(
                name="LM Neuquén",
                base_url="https://www.lmneuquen.com/",
                sitemap_url="https://www.lmneuquen.com/sitemap.xml", # Try sitemap first
                rss_url=None, # As requested
                crawl_strategy=models.CrawlStrategy.SITEMAP,
                rate_limit_ms=2000
            ),
            models.Site(
                name="Clarín",
                base_url="https://www.clarin.com/",
                sitemap_url="https://www.clarin.com/sitemap.xml",
                rss_url="https://www.clarin.com/rss/lo-ultimo/",
                crawl_strategy=models.CrawlStrategy.SITEMAP,
                rate_limit_ms=2000
            )
        ]
        
        for site in sites_to_create:
            if site.base_url not in existing_urls:
                print(f"Creating site: {site.name}")
                db.add(site)
            else:
                print(f"Site exists: {site.name}")
        
        # Default Settings
        settings_to_create = [
            models.Setting(key="scrape_interval_minutes", value="10"),
            models.Setting(key="lookback_days", value="30"),
        ]
        
        for s in settings_to_create:
            result = await db.execute(select(models.Setting).where(models.Setting.key == s.key))
            if not result.scalar_one_or_none():
                print(f"Creating setting: {s.key}")
                db.add(s)
        
        await db.commit()
        print("Seed completed.")

if __name__ == "__main__":
    asyncio.run(seed())
