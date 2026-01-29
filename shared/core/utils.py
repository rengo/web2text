import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'fbclid', 'yclid', '_ga', 'mc_cid', 'mc_eid'
}

def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL:
    - remove fragment
    - lowercase host
    - remove trailing slash (if path is not root)
    - sort query params
    - remove tracking params
    """
    try:
        parsed = urlparse(url)
        
        # 1. Lowercase host
        netloc = parsed.netloc.lower()
        
        # 2. Path: remove trailing slash unless it's just "/"
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path.rstrip('/')
        if not path:
            path = "/"
            
        # 3. Query: filter and sort
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = []
        for key, value in query_items:
            if key.lower() not in TRACKING_PARAMS:
                filtered_query.append((key, value))
        
        filtered_query.sort(key=lambda x: x[0])
        new_query = urlencode(filtered_query)
        
        # Reassemble, dropping fragment
        new_parts = (parsed.scheme, netloc, path, parsed.params, new_query, '')
        return urlunparse(new_parts)
        
    except Exception:
        return url

def compute_url_hash(url: str) -> str:
    """Compute SHA256 hash of canonical URL."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def compute_content_hash(text: str) -> str:
    """Compute SHA256 hash of text content."""
    if not text:
        return ""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
