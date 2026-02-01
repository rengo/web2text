import logging
import asyncio
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
import httpx
from bs4 import BeautifulSoup

from shared.core import models, database, utils
from worker.app.pipeline import DiscoveryPipeline
from worker.app.content_extractor import ContentExtractor
from worker.app.date_extractor import DateExtractor
from worker.app.logger import remote_logger

logger = logging.getLogger(__name__)

class ScraperEngine:
    def __init__(self):
        self.http_client = httpx.AsyncClient(headers={"User-Agent": "Web2TextBot/1.0"}, follow_redirects=True, timeout=30.0)
        self.discovery = DiscoveryPipeline(self.http_client)
        self.lookback_days = 30 # Default

    async def reload_settings(self, db):
        try:
            result = await db.execute(select(models.Setting).where(models.Setting.key == "lookback_days"))
            setting = result.scalar_one_or_none()
            if setting:
                self.lookback_days = int(setting.value)
                logger.info(f"ScraperEngine: Lookback days updated to {self.lookback_days}")
        except Exception as e:
            logger.error(f"Error reloading scraper settings: {e}")

    def _is_valid_article(self, html: str) -> bool:
        """
        Parses HTML for JSON-LD and checks if @type is NewsArticle, Article, BlogPosting, or Report.
        Returns True if a valid article type is found, False otherwise.
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            scripts = soup.find_all('script', type='application/ld+json')
            
            valid_types = {'NewsArticle', 'Article', 'BlogPosting', 'Report'}
            
            for script in scripts:
                if not script.string:
                    continue
                try:
                    data = json.loads(script.string)
                    # JSON-LD can be a list or a dict
                    if isinstance(data, dict):
                        data = [data]
                    
                    for item in data:
                        # item can be a dict, or we might need to look deeper if it's a graph
                        # Simple flat check first
                        item_type = item.get('@type')
                        
                        # Handle list of types
                        if isinstance(item_type, list):
                            if any(t in valid_types for t in item_type):
                                return True
                        elif item_type in valid_types:
                            return True
                            
                        # Handle @graph structure (often used by Yoast etc)
                        if '@graph' in item:
                            for node in item['@graph']:
                                node_type = node.get('@type')
                                if isinstance(node_type, list):
                                    if any(t in valid_types for t in node_type):
                                        return True
                                elif node_type in valid_types:
                                    return True
                except json.JSONDecodeError:
                    continue
                    
            return False
        except Exception as e:
            logger.error(f"Error validating article JSON-LD: {e}")
            return False


    async def run_discovery_phase(self, db, site: models.Site, run_id):
        """
        Discovers URLs and doing dedupe upserts.
        """
        # Ensure settings are current
        await self.reload_settings(db)
        
        await remote_logger.log(f"Starting discovery phase for {site.name}...", level="info", extra={"site_id": site.id, "run_id": run_id})
        discovered_urls = await self.discovery.run(site)
        
        # --- CAP DISCOVERY ---
        if len(discovered_urls) > 1000:
            logger.info(f"Site {site.name}: Capping discovery from {len(discovered_urls)} to 1000 URLs")
            await remote_logger.log(f"Capping discovery to 1000 URLs (found {len(discovered_urls)})", level="warning", extra={"site_id": site.id})
            discovered_urls = discovered_urls[:1000]
        # ----------------------

        logger.info(f"Site {site.name}: Upserting {len(discovered_urls)} URLs")
        await remote_logger.log(f"Upserting {len(discovered_urls)} URLs for {site.name}", level="info", extra={"site_id": site.id})
        
        total_discovered = len(discovered_urls)
        
        # Batch Upsert using Postgres ON CONFLICT
        if discovered_urls:
            now = datetime.now(timezone.utc)
            values = []
            for url in discovered_urls:
                values.append({
                    "site_id": site.id,
                    "url": url,
                    "canonical_url": url,
                    "url_hash": utils.compute_url_hash(url),
                    "discovered_via": models.DiscoverySource.SITEMAP,
                    "status": models.PageStatus.NEW,
                    "first_seen_at": now,
                    "last_seen_at": now
                })
            
            # Divide into chunks of 500 to avoid huge statements
            for i in range(0, len(values), 500):
                chunk = values[i:i+500]
                stmt = insert(models.Page).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['url_hash'],
                    set_={"last_seen_at": now}
                )
                await db.execute(stmt)
            
            await db.commit()
        
        # Update run stats
        await db.execute(
            update(models.ScrapeRun)
            .where(models.ScrapeRun.id == run_id)
            .values(pages_discovered=total_discovered)
        )
        await db.commit()

    async def run_processing_phase(self, db, site: models.Site, run_id, limit=200):
        """
        Process NEW pages.
        """
        # Ensure settings are current
        await self.reload_settings(db)
        
        await remote_logger.log(f"Starting processing phase for {site.name} (limit={limit})...", level="info", extra={"site_id": site.id, "run_id": run_id})
        
        # Fetch pages to scrape
        q = select(models.Page).where(
            models.Page.site_id == site.id,
            models.Page.status == models.PageStatus.NEW
        ).order_by(models.Page.first_seen_at.desc()).limit(limit)
        
        result = await db.execute(q)
        pages = result.scalars().all()
        
        if not pages:
            await remote_logger.log(f"No new pages to process for {site.name}", level="info", extra={"site_id": site.id})
        
        processed = 0
        failed = 0
        
        for page in pages:
            try:
                await self.process_page(db, page, site.id)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process {page.url}: {e}")
                await remote_logger.log(f"Failed to process {page.url}: {e}", level="error", extra={"site_id": site.id, "url": page.url})
                failed += 1
                page.status = models.PageStatus.FAILED
                page.error = str(e)
                db.add(page)
                await db.commit()
            
            # Rate limit
            await asyncio.sleep(site.rate_limit_ms / 1000.0)

        # Update run stats
        await db.execute(
            update(models.ScrapeRun)
            .where(models.ScrapeRun.id == run_id)
            .values(
                pages_processed=processed, 
                pages_failed=failed,
                finished_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()
        await remote_logger.log(f"Processing phase finished. Processed: {processed}, Failed: {failed}", level="info", extra={"site_id": site.id, "run_id": run_id})

    async def process_page(self, db, page: models.Page, site_id: int):
        logger.info(f"Scraping {page.url}")
        await remote_logger.log(f"Scraping {page.url}...", level="info", extra={"site_id": site_id, "url": page.url})
        
        resp = await self.http_client.get(page.url)
        page.http_status = resp.status_code
        
        if resp.status_code != 200:
            page.status = models.PageStatus.FAILED
            page.error = f"HTTP {resp.status_code}"
            db.add(page)
            await db.commit()
            await remote_logger.log(f"HTTP Error {resp.status_code} for {page.url}", level="error", extra={"site_id": site_id, "url": page.url})
            return

        html = resp.text
        
        # --- JSON-LD FILTER ---
        if not self._is_valid_article(html):
            logger.info(f"Skipping {page.url}: Not a valid article (JSON-LD check failed)")
            await remote_logger.log(f"Skipping {page.url}: Not a valid article", level="info", extra={"site_id": site_id, "url": page.url})
            page.status = models.PageStatus.SKIPPED
            page.error = "Filtered: Not an article (JSON-LD)"
            db.add(page)
            await db.commit()
            return
        # ---------------------

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Date Extraction
        published_at, date_source, conf = DateExtractor.extract(html, page.url, soup)
        
        # --- LOOKBACK FILTER ---
        if published_at:
            # Ensure published_at is aware for comparison
            p_at = published_at
            if p_at.tzinfo is None: p_at = p_at.replace(tzinfo=timezone.utc)
            
            threshold = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
            if p_at < threshold:
                logger.info(f"Skipping {page.url}: Older than {self.lookback_days} days ({p_at})")
                await remote_logger.log(f"Skipping {page.url}: Older than {self.lookback_days} days", level="info", extra={"site_id": site_id, "url": page.url})
                page.status = models.PageStatus.SKIPPED
                page.published_at = published_at
                db.add(page)
                await db.commit()
                return
        # ---------------------

        # 2. Content Extraction
        text, method_used = ContentExtractor.extract(html)
        
        # 3. Metadata Extraction
        from worker.app.metadata_extractor import MetadataExtractor
        meta = MetadataExtractor.extract(html, soup)
        
        title = meta.get("title") or (soup.title.string if soup.title else None)
        
        content_hash = utils.compute_content_hash(text)
        
        # Save Content
        new_content = models.PageContent(
            page_id=page.id,
            extracted_text=text,
            raw_html=html,
            metadata_={
                "date_source": date_source,
                "date_confidence": conf,
                "extraction_method": method_used,
                "og_title": title,
                "meta_extracted": True
            }
        )
        db.add(new_content)
        
        # Update Page
        page.status = models.PageStatus.PROCESSED
        page.title = title
        page.author = meta.get("author")
        page.summary = meta.get("summary")
        page.image_url = meta.get("image_url")
        page.language = meta.get("language")
        page.published_at = published_at
        page.scraped_at = datetime.now(timezone.utc)
        page.content_hash = content_hash
        
        db.add(page)
        await db.commit()
        await remote_logger.log(f"Successfully scraped {page.url}", level="success", extra={"site_id": site_id, "url": page.url})

    async def close(self):
        await self.http_client.aclose()
