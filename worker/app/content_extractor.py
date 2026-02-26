import json
import re
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
        # 0. Arc Publishing (Fusion CMS)
        try:
            if "Fusion.globalContent" in html:
                soup = BeautifulSoup(html, 'html.parser')
                scripts = soup.find_all('script')
                for s in scripts:
                    script_content = s.string
                    if script_content and script_content.startswith("window.Fusion="):
                        match = re.search(r'Fusion\.globalContent\s*=\s*(\{.*?\});\s*(?:Fusion|$)', script_content)
                        if match:
                            fusion_data = json.loads(match.group(1))
                            elements = fusion_data.get("content_elements", [])
                            text_blocks = []
                            for el in elements:
                                if el.get("type") == "text":
                                    raw_text = el.get("content", "")
                                    clean_text = BeautifulSoup(raw_text, "html.parser").get_text(separator='\n', strip=True)
                                    text_blocks.append(clean_text)
                                elif el.get("type") == "list":
                                    for item in el.get("items", []):
                                        if item.get("type") == "text":
                                            clean_val = BeautifulSoup(item.get("content", ""), "html.parser").get_text(separator='\n', strip=True)
                                            text_blocks.append(f"- {clean_val}")

                            fusion_text = "\n\n".join(text_blocks)
                            if len(fusion_text) >= ContentExtractor.MIN_TEXT_LENGTH:
                                return fusion_text, "arc_fusion"
        except Exception:
            pass

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
