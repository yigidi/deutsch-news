import feedparser
import requests
import hashlib
import re
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from typing import List, Dict, Optional
import logging
from backend.config import NEWS_SOURCES, MAX_ARTICLES_PER_SOURCE

logger = logging.getLogger(__name__)

def sanitize_id(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    text = re.sub(r'_+', '_', text)
    return text.strip('_')[:100]

class NewsFetcher:
    def __init__(self):
        self.sources = NEWS_SOURCES
    
    def fetch_all(self) -> List[Dict]:
        all_articles = []
        for source_id, source_config in self.sources.items():
            try:
                articles = self.fetch_source(source_id, source_config)
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {source_config['name']}")
            except Exception as e:
                logger.error(f"Error fetching from {source_config['name']}: {e}")
        return all_articles
    
    def fetch_source(self, source_id: str, config: Dict) -> List[Dict]:
        if config["type"] == "rss":
            return self._fetch_rss(source_id, config)
        return []
    
    def _fetch_rss(self, source_id: str, config: Dict) -> List[Dict]:
        feed = feedparser.parse(config["url"])
        articles = []
        
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            try:
                content = self._extract_content(entry)
                if not content or len(content) < 100:
                    continue
                
                lang = self._detect_language(content)
                
                link = entry.get("link", "")
                entry_id = entry.get('id', link)
                safe_id = sanitize_id(entry_id)
                article_id = f"{source_id}_{safe_id}"
                
                article = {
                    "id": article_id,
                    "source_id": source_id,
                    "source_name": config["name"],
                    "source_url": link,
                    "title": entry.get("title", "").strip(),
                    "content": content,
                    "original_language": lang,
                    "published": entry.get("published", ""),
                    "author": entry.get("author", "")
                }
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error processing entry: {e}")
                continue
        
        return articles
    
    def _extract_content(self, entry) -> str:
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary
        elif hasattr(entry, "description"):
            content = entry.description
        
        if content:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(separator=" ", strip=True)
        
        return content
    
    def _detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = NewsFetcher()
    articles = fetcher.fetch_all()
    print(f"Total articles fetched: {len(articles)}")
    for a in articles[:3]:
        print(f"- {a['title'][:60]}... ({a['original_language']})")