from datetime import datetime
from typing import Optional, Tuple
import dateutil.parser
import re
import json

class DateExtractor:
    """
    Extracts publication date with strict priority:
    1. Metadata (OG, Parsely)
    2. Meta Name (date, pubdate)
    3. Time tag
    4. JSON-LD
    5. URL Pattern (Fallback)
    """

    @staticmethod
    def extract(html: str, url: str, soup) -> Tuple[Optional[datetime], str, str]:
        """
        Returns (dt, source, confidence)
        confidence: high, medium, low
        """
        
        # 1. Metadata High Confidence
        meta_targets = [
            {'property': 'article:published_time'},
            {'property': 'og:published_time'},
            {'name': 'parsely-pub-date'},
            {'name': 'citation_publication_date'},
            {'name': 'dc.date.issued'},
        ]
        
        for attrs in meta_targets:
            tag = soup.find('meta', attrs=attrs)
            if tag and tag.get('content'):
                dt = DateExtractor._parse_date(tag['content'])
                if dt:
                    return dt, f"meta_{list(attrs.values())[0]}", "high"

        # 2. Meta Name generic
        for name in ['date', 'pubdate', 'datePublished']:
            tag = soup.find('meta', attrs={'name': name}) or soup.find('meta', attrs={'itemprop': name})
            if tag and tag.get('content'):
                dt = DateExtractor._parse_date(tag['content'])
                if dt:
                    return dt, f"meta_{name}", "high"

        # 3. Time tag
        time_tag = soup.find('time')
        if time_tag:
            if time_tag.get('datetime'):
                dt = DateExtractor._parse_date(time_tag['datetime'])
                if dt:
                    return dt, "time_tag_datetime", "medium"
            # Text content fallback for time tag? risky.

        # 4. JSON-LD (Search for datePublished)
        # Often in <script type="application/ld+json">
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] # Try first
                if isinstance(data, dict):
                    date_str = data.get('datePublished') or data.get('dateCreated')
                    if date_str:
                         dt = DateExtractor._parse_date(date_str)
                         if dt:
                             return dt, "json_ld", "high"
                    
                    # Nested graph?
                    if '@graph' in data:
                        for item in data['@graph']:
                             if 'datePublished' in item:
                                 dt = DateExtractor._parse_date(item['datePublished'])
                                 if dt:
                                     return dt, "json_ld_graph", "high"
            except:
                pass

        # 5. URL Pattern (Low confidence)
        # /2024/01/29/
        match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if match:
            try:
                dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                return dt, "url_pattern", "low"
            except:
                pass
        
        return None, "none", "none"

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        try:
            from datetime import timezone
            dt = dateutil.parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except:
            return None
