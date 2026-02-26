import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import logging

# Mock logging
logger = logging.getLogger(__name__)

class Validator:
    def _is_valid_article(self, html: str) -> bool:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            scripts = soup.find_all('script', type='application/ld+json')
            valid_types = {'NewsArticle', 'Article', 'BlogPosting', 'Report'}
            for script in scripts:
                content = script.get_text()
                if not content: continue
                try:
                    data = json.loads(content, strict=False)
                    if isinstance(data, dict): data = [data]
                    for item in data:
                        item_type = item.get('@type')
                        if isinstance(item_type, list):
                            if any(t in valid_types for t in item_type): return True
                        elif item_type in valid_types: return True
                except: continue
            
            og_type = soup.find('meta', property='og:type') or soup.find('meta', attrs={'name': 'og:type'})
            if og_type and og_type.get('content', '').lower() == 'article':
                return True
            return False
        except Exception as e:
            return False

async def main():
    url = "https://www.boletinoficial.gob.ar/detalleAviso/primera/338750/20260226"
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True) as client:
        resp = await client.get(url)
        v = Validator()
        result = v._is_valid_article(resp.text)
        print(f"URL: {url}")
        print(f"VALID ARTICLE: {result}")

if __name__ == '__main__':
    asyncio.run(main())
