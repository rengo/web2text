import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Set, Optional
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
        self.blacklist_patterns = [
            "/category/", "/tag/", "/archive/", "/author/", "/page/", "/search/", "/search?",
            "/etiqueta/", "/categoria/", "/autor/", "/pag/", "/busqueda/", "/busqueda?", "/tema/" # Spanish common patterns
        ]

    def _is_valid_url(self, url: str) -> bool:
        """
        Checks if the URL is valid by ensuring it doesn't contain blacklisted patterns.
        """
        for pattern in self.blacklist_patterns:
            if pattern in url:
                return False
        return True

    async def run(self, site: Site, lookback_days: int = 30) -> List[str]:
        urls = set()
        
        # 0. Auto-discover sitemap if missing
        if not site.sitemap_url:
            logger.info(f"Sitemap URL missing for {site.name}, attempting auto-discovery...")
            discovered_sitemap = await self._discover_sitemap(site.base_url)
            if discovered_sitemap:
                logger.info(f"Discovered sitemap for {site.name}: {discovered_sitemap}")
                site.sitemap_url = discovered_sitemap
                # Note: We don't save to DB here as 'site' is often a detached or temporary object 
                # depending on how the caller handles sessions, but it will be used for this run.
        
        # 1. Sitemap Strategy
        if site.sitemap_url:
            logger.info(f"Trying sitemap for {site.name}: {site.sitemap_url}")
            sitemap_urls = await self._fetch_sitemap(site.sitemap_url, lookback_days)
            if sitemap_urls:
                logger.info(f"Found {len(sitemap_urls)} URLs via sitemap")
                urls.update(sitemap_urls)
            else:
                logger.warning(f"Sitemap failed or empty for {site.name}")

        # 2. RSS Strategy
        if site.rss_url:
            logger.info(f"Trying RSS for {site.name}: {site.rss_url}")
            rss_urls = await self._fetch_rss(site.rss_url, lookback_days)
            if rss_urls:
                logger.info(f"Found {len(rss_urls)} URLs via RSS")
                urls.update(rss_urls)
        
        # 3. Links Strategy
        # We always check the home page for links, especially if other sources are thin
        logger.info(f"Adding Links crawl for {site.name}")
        link_urls = await self._fetch_links(site.base_url)
        urls.update(link_urls)
        
        return list(urls)

    async def _discover_sitemap(self, base_url: str) -> Optional[str]:
        """Attempts to find a sitemap by checking robots.txt and common paths."""
        # 1. Try robots.txt
        try:
            robots_url = str(httpx.URL(base_url).join("robots.txt"))
            resp = await self.client.get(robots_url, timeout=5.0)
            if resp.status_code == 200:
                import re
                matches = re.findall(r'^Sitemap:\s*(.*)$', resp.text, re.MULTILINE | re.IGNORECASE)
                if matches:
                    # Return the first one found
                    logger.info(f"Sitemap found in robots.txt: {matches[0].strip()}")
                    return matches[0].strip()
        except Exception as e:
            logger.debug(f"Error checking robots.txt for {base_url}: {e}")

        # 2. Try common paths
        common_paths = ["sitemap.xml", "sitemap_index.xml", "sitemap/"]
        for path in common_paths:
            url = str(httpx.URL(base_url).join(path))
            try:
                # Use HEAD first for efficiency
                resp = await self.client.head(url, timeout=5.0)
                if resp.status_code == 200 and "xml" in resp.headers.get("content-type", "").lower():
                    return url
                
                # Some servers block HEAD or return wrong content-type, try GET
                resp = await self.client.get(url, timeout=5.0)
                if resp.status_code == 200 and ("<urlset" in resp.text or "<sitemapindex" in resp.text):
                    return url
            except Exception:
                continue
        return None

    async def _fetch_sitemap(self, url: str, lookback_days: int) -> Set[str]:
        # Minimal sitemap parser (handles sitemap index recursively 1 level)
        urls = set()
        threshold = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
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
                        subset = await self._fetch_sitemap(loc.text.strip(), lookback_days)
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
                         # Filter pattern
                         raw_url = loc.text.strip()
                         if not self._is_valid_url(raw_url):
                             continue
                             
                         c_url = canonicalize_url(raw_url)
                         urls.add(c_url)
        except Exception as e:
            logger.error(f"Sitemap error at {url}: {e}")
            
        return urls

    async def _fetch_rss(self, url: str, lookback_days: int) -> Set[str]:
        urls = set()
        threshold = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        try:
            # feedparser is blocking, run in executor
            feed = await asyncio.to_thread(feedparser.parse, url)
            for entry in feed.entries:
                if 'published_parsed' in entry:
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    if dt < threshold:
                        continue
                
                if 'link' in entry:
                    if not self._is_valid_url(entry.link):
                        continue
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
                    if not self._is_valid_url(full_url):
                        continue
                    c_url = canonicalize_url(full_url)
                    urls.add(c_url)
        except Exception as e:
             logger.error(f"Links crawl error: {e}")
        return urls
