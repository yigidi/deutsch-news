import feedparser
import requests
import hashlib
import re
import time
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
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
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
                link = entry.get("link", "")
                if not link:
                    continue
                
                # Get full article content by scraping the page
                full_content = self._fetch_full_article(link, source_id)
                if not full_content or len(full_content) < 200:
                    # Fallback to RSS content
                    full_content = self._extract_rss_content(entry)
                
                if not full_content or len(full_content) < 200:
                    continue
                
                lang = self._detect_language(full_content)
                
                entry_id = entry.get('id', link)
                safe_id = sanitize_id(entry_id)
                article_id = f"{source_id}_{safe_id}"
                
                article = {
                    "id": article_id,
                    "source_id": source_id,
                    "source_name": config["name"],
                    "source_url": link,
                    "title": entry.get("title", "").strip(),
                    "content": full_content,
                    "original_language": lang,
                    "published": entry.get("published", ""),
                    "author": entry.get("author", "")
                }
                articles.append(article)
                
                # Be polite - small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error processing entry: {e}")
                continue
        
        return articles
    
    def _fetch_full_article(self, url: str, source_id: str) -> Optional[str]:
        """Fetch and extract full article content from the actual page"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Source-specific selectors for article content
            selectors = self._get_content_selectors(source_id)
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    # Get the largest text block
                    best_text = max((el.get_text(separator=' ', strip=True) for el in elements), key=len, default="")
                    if len(best_text) > 200:
                        return self._clean_text(best_text)
            
            # Generic fallback: find article/main content
            for tag in ['article', 'main', '[role="main"]', '.article-content', '.post-content', '.entry-content']:
                el = soup.select_one(tag)
                if el:
                    text = el.get_text(separator=' ', strip=True)
                    if len(text) > 200:
                        return self._clean_text(text)
            
            return None
            
        except Exception as e:
            logger.debug(f"Full article fetch failed for {url}: {e}")
            return None
    
    def _get_content_selectors(self, source_id: str) -> List[str]:
        """Source-specific CSS selectors for article content"""
        selectors_map = {
            'tagesschau': ['.textabsatz', '.article-body', '#content'],
            'dw': ['.article-body', '.longText', '.rte'],
            'spiegel': ['.article-section', '.RichText', '[data-area="article-body"]'],
            'zeit': ['.article-body', '.content-body', '.zon-teaser__text'],
            'bbc': ['[data-component="text-block"]', '.article-body', '.story-body'],
            'reuters': ['.article-body__content', '.ArticleBody', '[data-testid="paragraph"]'],
            'sozcu': ['.news-content', '.article-content', '.content-detail'],
            'hurriyet': ['.news-content', '.article-body', '.content'],
            'milliyet': ['.news-content', '.article-body', '.yazi_icerik'],
            'haberturk': ['.news-content', '.article-body', '.content'],
            'cnnturk': ['.article-content', '.news-content', '.content'],
        }
        return selectors_map.get(source_id, ['.article-content', '.content', 'article', 'main'])
    
    def _extract_rss_content(self, entry) -> str:
        """Extract content from RSS entry as fallback"""
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
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common boilerplate
        text = re.sub(r'(Cookie|cookie|Cerez|cerez|GDPR|KVKK|Accept|Kabul|Reklam|Advertisement).*?(?=\.|$)', '', text, flags=re.IGNORECASE)
        # Remove very short sentences (likely nav/UI)
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        return '. '.join(sentences) + '.'
    
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
        print(f"- {a['title'][:60]}... ({a['original_language']}) len={len(a['content'])}")