import trafilatura
from bs4 import BeautifulSoup

class ContentExtractor:
    """
    Extracts main content from HTML.
    Primary: Trafilatura
    Fallback: BeautifulSoup heuristics
    """
    
    MIN_TEXT_LENGTH = 100

    @staticmethod
    def extract(html: str) -> tuple[str, str]:
        """
        Returns (extracted_text, method_used)
        """
        # 1. Trafilatura
        try:
            text = trafilatura.extract(html, include_tables=False, include_comments=False)
            if text and len(text) >= ContentExtractor.MIN_TEXT_LENGTH:
                return text, "trafilatura"
        except Exception:
            pass
            
        # 2. BS4 Fallback
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()

        # Try specific tags
        article = soup.find('article')
        if article:
            text = article.get_text(separator='\n', strip=True)
            if len(text) >= ContentExtractor.MIN_TEXT_LENGTH:
                return text, "bs4_article"
                
        # Try generic body paragraphs
        body = soup.find('body')
        if body:
            paragraphs = body.find_all('p')
            text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
            text = "\n\n".join(text_blocks)
            if len(text) >= ContentExtractor.MIN_TEXT_LENGTH:
                return text, "bs4_paragraphs"
                
        return "", "failed"
