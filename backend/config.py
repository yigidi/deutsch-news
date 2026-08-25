import os
from dotenv import load_dotenv

load_dotenv()

NEWS_SOURCES = {
    "tagesschau": {
        "name": "Tagesschau",
        "url": "https://www.tagesschau.de/xml/rss2/",
        "type": "rss",
        "language": "de"
    },
    "dw": {
        "name": "Deutsche Welle",
        "url": "https://rss.dw.com/rdf/rss-de-all",
        "type": "rss",
        "language": "de"
    },
    "spiegel": {
        "name": "Der Spiegel",
        "url": "https://www.spiegel.de/schlagzeilen/tops/index.rss",
        "type": "rss",
        "language": "de"
    },
    "zeit": {
        "name": "Die Zeit",
        "url": "https://newsfeed.zeit.de/index",
        "type": "rss",
        "language": "de"
    },
    "bbc": {
        "name": "BBC News",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "type": "rss",
        "language": "en"
    },
    "reuters": {
        "name": "Reuters",
        "url": "https://www.reuters.com/world/rss",
        "type": "rss",
        "language": "en"
    }
}

CEFR_LEVELS = {
    "de": ["A1", "A2", "B1", "B2", "Original"],
    "other": ["C1"]
}

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "audio")

MAX_ARTICLES_PER_SOURCE = 5
UPDATE_INTERVAL_HOURS = 6