import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Set
from shared.core.models import Site, CrawlStrategy
from shared.core.utils import canonicalize_url
import httpx
from bs4 import BeautifulSoup
import feedparser
import dateutil.parser

logger = logging.getLogger(__name__)

class DiscoveryPipeline:
    """
    Implements the discovery strategy: Sitemap -> RSS -> Links
    Returns a list of discovered URLs (canonicalized).
    """
    
    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    async def run(self, site: Site) -> List[str]:
        urls = set()
        
        # 1. Sitemap Strategy
        if site.sitemap_url:
            logger.info(f"Trying sitemap for {site.name}: {site.sitemap_url}")
            sitemap_urls = await self._fetch_sitemap(site.sitemap_url)
            if sitemap_urls:
                logger.info(f"Found {len(sitemap_urls)} URLs via sitemap")
                return list(sitemap_urls)
            logger.warning(f"Sitemap failed or empty for {site.name}")

        # 2. RSS Strategy (fallback if sitemap empty/fail and rss configured)
        if site.rss_url:
            logger.info(f"Trying RSS for {site.name}: {site.rss_url}")
            rss_urls = await self._fetch_rss(site.rss_url)
            if rss_urls:
                logger.info(f"Found {len(rss_urls)} URLs via RSS")
                return list(rss_urls)
        
        # 3. Links Strategy (Final fallback)
        # Only if explicitly allowed or if it's the strategy? 
        # Prompt says: "Si sitemap y rss no dan resultados: Estrategia links"
        logger.info(f"Falling back to Links crawl for {site.name}")
        link_urls = await self._fetch_links(site.base_url)
        return list(link_urls)

    async def _fetch_sitemap(self, url: str) -> Set[str]:
        # Minimal sitemap parser (handles sitemap index recursively 1 level)
        urls = set()
        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        
        try:
            response = await self.client.get(url, timeout=30.0)
            if response.status_code != 200:
                return set()
            
            soup = BeautifulSoup(response.content, 'xml')
            
            # Check if index
            sitemaps = soup.find_all('sitemap')
            if sitemaps:
                # Is index, fetch children
                for sm in sitemaps: 
                    loc = sm.find('loc')
                    lastmod = sm.find('lastmod')
                    
                    # If index has lastmod, can skip entire branch?
                    if lastmod:
                        try:
                            dt = dateutil.parser.parse(lastmod.text.strip())
                            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                            if dt < threshold:
                                continue
                        except: pass
                        
                    if loc:
                        subset = await self._fetch_sitemap(loc.text.strip())
                        urls.update(subset)
            else:
                # Is urlset
                for u in soup.find_all('url'):
                    loc = u.find('loc')
                    lastmod = u.find('lastmod')
                    
                    if lastmod:
                        try:
                            dt = dateutil.parser.parse(lastmod.text.strip())
                            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                            if dt < threshold:
                                continue
                        except: pass
                        
                    if loc:
                         c_url = canonicalize_url(loc.text.strip())
                         urls.add(c_url)
        except Exception as e:
            logger.error(f"Sitemap error at {url}: {e}")
            
        return urls

    async def _fetch_rss(self, url: str) -> Set[str]:
        urls = set()
        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        try:
            # feedparser is blocking, run in executor
            feed = await asyncio.to_thread(feedparser.parse, url)
            for entry in feed.entries:
                if 'published_parsed' in entry:
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    if dt < threshold:
                        continue
                
                if 'link' in entry:
                    c_url = canonicalize_url(entry.link)
                    urls.add(c_url)
        except Exception as e:
             logger.error(f"RSS error: {e}")
        return urls

    async def _fetch_links(self, url: str) -> Set[str]:
        urls = set()
        try:
            response = await self.client.get(url, timeout=20.0)
            soup = BeautifulSoup(response.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Normalize absolute
                full_url = str(httpx.URL(url).join(href))
                # Basic Host check
                if httpx.URL(full_url).host == httpx.URL(url).host:
                    c_url = canonicalize_url(full_url)
                    urls.add(c_url)
        except Exception as e:
             logger.error(f"Links crawl error: {e}")
        return urls
