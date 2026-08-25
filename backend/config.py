import os
from dotenv import load_dotenv

load_dotenv()

NEWS_SOURCES = {
    "tagesschau": {"name": "Tagesschau", "url": "https://www.tagesschau.de/xml/rss2/", "type": "rss", "language": "de"},
    "dw": {"name": "Deutsche Welle", "url": "https://rss.dw.com/rdf/rss-de-all", "type": "rss", "language": "de"},
    "spiegel": {"name": "Der Spiegel", "url": "https://www.spiegel.de/schlagzeilen/tops/index.rss", "type": "rss", "language": "de"},
    "zeit": {"name": "Die Zeit", "url": "https://newsfeed.zeit.de/index", "type": "rss", "language": "de"},
    "bbc": {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "type": "rss", "language": "en"},
    "reuters": {"name": "Reuters", "url": "https://www.reuters.com/world/rss", "type": "rss", "language": "en"},
    "sozcu": {"name": "Sözcü", "url": "https://www.sozcu.com.tr/feeds/rss", "type": "rss", "language": "tr"},
    "hurriyet": {"name": "Hürriyet", "url": "https://www.hurriyet.com.tr/rss/anasayfa", "type": "rss", "language": "tr"},
    "milliyet": {"name": "Milliyet", "url": "https://www.milliyet.com.tr/rss/rssNew/anasayfa.xml", "type": "rss", "language": "tr"},
    "haberturk": {"name": "Habertürk", "url": "https://www.haberturk.com/rss", "type": "rss", "language": "tr"},
    "cnnturk": {"name": "CNN Türk", "url": "https://www.cnnturk.com/feeds/rss", "type": "rss", "language": "tr"},
    "ntv": {"name": "NTV", "url": "https://www.ntv.com.tr/son-dakika.rss", "type": "rss", "language": "tr"},
    "trthaber": {"name": "TRT Haber", "url": "https://www.trthaber.com/rss.xml", "type": "rss", "language": "tr"},
}

CEFR_LEVELS = {
    "de": ["A1", "A2", "B1", "B2", "Original"],
    "other": ["C1"]
}

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "audio")

MAX_ARTICLES_PER_SOURCE = 3
UPDATE_INTERVAL_HOURS = 6