import trafilatura
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

class MetadataExtractor:
    @staticmethod
    def extract(html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extracts metadata: author, summary, image_url, language.
        """
        result = {
            "title": None,
            "author": None,
            "summary": None,
            "image_url": None,
            "language": None
        }

        # 1. Try Trafilatura for metadata
        try:
            # metadata in trafilatura 1.8+ is accessed via extract_metadata
            # It returns a metadata object with attributes like author, title, date, etc.
            metadata = trafilatura.extract_metadata(html)
            if metadata:
                result["title"] = getattr(metadata, 'title', None)
                result["author"] = getattr(metadata, 'author', None)
                result["summary"] = getattr(metadata, 'description', None)
                result["image_url"] = getattr(metadata, 'image', None)
                result["language"] = getattr(metadata, 'language', None)
        except Exception:
            pass

        # 2. BeautifulSoup fallbacks/refinements
        
        # Title Fallback
        if not result["title"]:
            title_tag = (
                soup.find("meta", property="og:title") or 
                soup.find("meta", attrs={"name": "twitter:title"})
            )
            if title_tag:
                result["title"] = title_tag.get("content")
        
        # Author Fallback
        if not result["author"]:
            author_tag = (
                soup.find("meta", attrs={"name": "author"}) or 
                soup.find("meta", property="article:author") or
                soup.find("meta", attrs={"name": "twitter:creator"})
            )
            if author_tag:
                result["author"] = author_tag.get("content")

        # Summary Fallback
        if not result["summary"]:
            desc_tag = (
                soup.find("meta", attrs={"name": "description"}) or 
                soup.find("meta", property="og:description") or
                soup.find("meta", attrs={"name": "twitter:description"})
            )
            if desc_tag:
                result["summary"] = desc_tag.get("content")

        # Image Fallback
        if not result["image_url"]:
            img_tag = (
                soup.find("meta", property="og:image") or 
                soup.find("meta", attrs={"name": "twitter:image"}) or
                soup.find("link", rel="image_src")
            )
            if img_tag:
                result["image_url"] = img_tag.get("content") or img_tag.get("href")

        # Language Fallback
        if not result["language"]:
            html_tag = soup.find("html")
            if html_tag and html_tag.get("lang"):
                result["language"] = html_tag.get("lang")
            else:
                lang_tag = soup.find("meta", attrs={"http-equiv": "content-language"}) or soup.find("meta", attrs={"name": "language"})
                if lang_tag:
                    result["language"] = lang_tag.get("content")

        return result
