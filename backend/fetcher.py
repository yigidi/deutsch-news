import feedparser
import requests
import re
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

NEWS_SOURCES = {
    "tagesschau": {"name": "Tagesschau", "url": "https://www.tagesschau.de/xml/rss2/", "language": "de"},
    "dw": {"name": "Deutsche Welle", "url": "https://rss.dw.com/rdf/rss-de-all", "language": "de"},
    "spiegel": {"name": "Der Spiegel", "url": "https://www.spiegel.de/schlagzeilen/tops/index.rss", "language": "de"},
    "zeit": {"name": "Die Zeit", "url": "https://newsfeed.zeit.de/index", "language": "de"},
    "bbc": {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "language": "en"},
    "reuters": {"name": "Reuters", "url": "https://www.reuters.com/world/rss", "language": "en"},
    "sozcu": {"name": "Sözcü", "url": "https://www.sozcu.com.tr/feeds/rss", "language": "tr"},
    "hurriyet": {"name": "Hürriyet", "url": "https://www.hurriyet.com.tr/rss/anasayfa", "language": "tr"},
    "milliyet": {"name": "Milliyet", "url": "https://www.milliyet.com.tr/rss/rssNew/anasayfa.xml", "language": "tr"},
    "haberturk": {"name": "Habertürk", "url": "https://www.haberturk.com/rss", "language": "tr"},
    "cnnturk": {"name": "CNN Türk", "url": "https://www.cnnturk.com/feeds/rss", "language": "tr"},
    "ntv": {"name": "NTV", "url": "https://www.ntv.com.tr/son-dakika.rss", "language": "tr"},
    "trthaber": {"name": "TRT Haber", "url": "https://www.trthaber.com/rss.xml", "language": "tr"},
}

MAX_ARTICLES_PER_SOURCE = 3

SELECTORS = {
    "tagesschau": [".textabsatz", "#content .article-body"],
    "dw": [".article-body", ".rte", ".longText"],
    "spiegel": [".article-section", "[data-area='article-body']"],
    "zeit": [".article-body", ".content-body"],
    "bbc": ["[data-component='text-block']", ".article-body"],
    "reuters": [".article-body__content", "[data-testid='paragraph']"],
    "sozcu": [".news-content", ".article-content"],
    "hurriyet": [".news-content", ".article-body"],
    "milliyet": [".news-content", ".yazi_icerik"],
    "haberturk": [".news-content", ".article-body"],
    "cnnturk": [".article-content", ".news-content"],
    "ntv": [".news-content", ".article-body"],
    "trthaber": [".news-content", ".article-body"],
}

def clean_id(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    return re.sub(r'_+', '_', text).strip('_')[:100]

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(Cookie|Cerez|GDPR|KVKK|Accept|Kabul|Reklam|Advertisement).*?(?=\.|$)', '', text, flags=re.IGNORECASE)
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    return '. '.join(sentences) + '.'

def detect_lang(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

class NewsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_all(self) -> List[Dict]:
        all_articles = []
        for src_id, config in NEWS_SOURCES.items():
            try:
                articles = self._fetch_rss(src_id, config)
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} from {config['name']}")
            except Exception as e:
                logger.error(f"Error fetching {config['name']}: {e}")
        return all_articles

    def _fetch_rss(self, src_id: str, config: Dict) -> List[Dict]:
        feed = feedparser.parse(config["url"])
        articles = []
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            try:
                link = entry.get("link", "")
                if not link:
                    continue
                
                full_content = self._scrape_article(link, src_id)
                if not full_content or len(full_content) < 200:
                    full_content = self._rss_fallback(entry)
                
                if not full_content or len(full_content) < 200:
                    continue
                
                lang = detect_lang(full_content)
                article_id = f"{src_id}_{clean_id(entry.get('id', link))}"
                
                articles.append({
                    "id": article_id,
                    "source_id": src_id,
                    "source_name": config["name"],
                    "source_url": link,
                    "title": entry.get("title", "").strip(),
                    "content": full_content,
                    "original_language": lang,
                    "published": entry.get("published", ""),
                })
            except Exception as e:
                logger.warning(f"Error processing entry: {e}")
        return articles

    def _scrape_article(self, url: str, src_id: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            for selector in SELECTORS.get(src_id, ['article', 'main', '.content', '.article-body']):
                elements = soup.select(selector)
                if elements:
                    best = max((el.get_text(' ', strip=True) for el in elements), key=len, default="")
                    if len(best) > 200:
                        return clean_text(best)
            
            return None
        except Exception:
            return None

    def _rss_fallback(self, entry) -> str:
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary
        elif hasattr(entry, "description"):
            content = entry.description
        if content:
            soup = BeautifulSoup(content, "html.parser")
            return clean_text(soup.get_text(' ', strip=True))
        return ""