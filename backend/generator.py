import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from backend.config import OUTPUT_DIR, DATA_DIR
from backend.fetcher import NewsFetcher
from backend.ai_processor import AIProcessor
from backend.tts import TTSGenerator

logger = logging.getLogger(__name__)

class SiteGenerator:
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.processor = AIProcessor()
        self.tts = TTSGenerator()
        self.output_dir = OUTPUT_DIR
        self.data_dir = DATA_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def generate(self):
        logger.info("Starting site generation...")
        
        articles = self.fetcher.fetch_all()
        logger.info(f"Fetched {len(articles)} articles")
        
        processed_articles = []
        for i, article in enumerate(articles):
            logger.info(f"Processing article {i+1}/{len(articles)}: {article['title'][:50]}...")
            article = self.processor.process_article(article)
            audio_map = self.tts.generate_for_article(article)
            article["audio"] = audio_map
            processed_articles.append(article)
        
        self._save_articles(processed_articles)
        self._generate_html(processed_articles)
        self._copy_static_assets()
        
        logger.info(f"Site generated successfully in {self.output_dir}")
    
    def _save_articles(self, articles: List[Dict]):
        data_file = os.path.join(self.data_dir, "articles.json")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} articles to {data_file}")
    
    def _generate_html(self, articles: List[Dict]):
        index_html = self._render_index(articles)
        with open(os.path.join(self.output_dir, "index.html"), 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        for article in articles:
            article_html = self._render_article(article)
            article_file = os.path.join(self.output_dir, f"article_{article['id']}.html")
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(article_html)
    
    def _render_index(self, articles: List[Dict]) -> str:
        from backend.config import NEWS_SOURCES
        articles_html = ""
        for article in articles:
            first_version = list(article["versions"].keys())[0] if article["versions"] else "A1"
            articles_html += f"""
            <article class="news-card" data-id="{article['id']}">
                <h2><a href="article_{article['id']}.html">{article['title']}</a></h2>
                <div class="meta">
                    <span class="source">{article['source_name']}</span>
                    <span class="lang">{article['original_language'].upper()}</span>
                </div>
                <p class="preview">{article['versions'].get(first_version, {}).get('content', '')[:200]}...</p>
                <div class="levels">
                    {''.join(f'<span class="level-badge">{lvl}</span>' for lvl in article['versions'].keys())}
                </div>
            </article>"""
        
        source_options = ''.join(f'<option value="{k}">{v["name"]}</option>' for k, v in NEWS_SOURCES.items())
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deutsch Lernen mit Nachrichten</title>
    <link rel="stylesheet" href="static/css/style.css">
</head>
<body>
    <header>
        <h1>📰 Deutsch Lernen mit Nachrichten</h1>
        <p class="subtitle">Aktuelle Nachrichten in deinem Sprachniveau (A1-C1)</p>
    </header>
    <main>
        <div class="filters">
            <select id="levelFilter" onchange="filterByLevel(this.value)">
                <option value="">Alle Niveaus</option>
                <option value="A1">A1</option>
                <option value="A2">A2</option>
                <option value="B1">B1</option>
                <option value="B2">B2</option>
                <option value="C1">C1</option>
                <option value="Original">Original</option>
            </select>
            <select id="sourceFilter" onchange="filterBySource(this.value)">
                <option value="">Alle Quellen</option>
                {source_options}
            </select>
        </div>
        <div id="articles" class="articles-grid">
            {articles_html}
        </div>
    </main>
    <footer>
        <p>Daten aktualisiert: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    </footer>
    <script src="static/js/main.js"></script>
</body>
</html>"""
    
    def _render_article(self, article: Dict) -> str:
        versions_html = ""
        ai_errors = []
        for level, version in article["versions"].items():
            audio_src = article.get("audio", {}).get(level, "")
            audio_html = f'<audio controls src="{audio_src}"></audio>' if audio_src else '<span class="no-audio">🔊 Audio wird generiert...</span>'
            
            is_original = level == "Original"
            orig_lang = article.get("original_language", "de")
            
            # Check for AI errors
            ai_error = version.get("_ai_error")
            if ai_error:
                ai_errors.append(f"{level}: {ai_error}")
                error_banner = f'<div class="ai-error-banner">⚠️ AI işlemi başarısız: {ai_error}</div>'
            else:
                error_banner = ""
            
            versions_html += f"""
            <section class="version-panel" data-level="{level}">
                <div class="version-header">
                    <h3>{level} {'(Original)' if is_original else ''}</h3>
                    {audio_html}
                </div>
                <h4>{version.get('title', article['title'])}</h4>
                <div class="version-content" data-lang="{orig_lang if is_original else 'de'}">
                    {error_banner}
                    {self._format_content(version.get('content', ''), orig_lang if is_original else 'de')}
                </div>
            </section>"""
        
        source_link = f'<a href="{article["source_url"]}" target="_blank" rel="noopener">Quelle: {article["source_name"]}</a>'
        tab_buttons = ''.join(f'<button class="tab-btn" data-level="{lvl}" onclick="showLevel(\'{lvl}\')">{lvl}</button>' for lvl in article['versions'].keys())
        
        # Global AI error banner
        global_error = ""
        if ai_errors:
            global_error = f'<div class="global-ai-error"><strong>⚠️ AI İşleme Hataları:</strong><ul>{"".join(f"<li>{e}</li>" for e in ai_errors)}</ul></div>'
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']} - Deutsch Lernen</title>
    <link rel="stylesheet" href="static/css/style.css">
</head>
<body>
    <header>
        <a href="index.html" class="back-link">← Zurück</a>
        <h1>{article['title']}</h1>
        <div class="article-meta">
            <span>Quelle: {article['source_name']}</span>
            <span>Sprache: {article['original_language'].upper()}</span>
        </div>
    </header>
    <main>
        {global_error}
        <div class="level-tabs">
            {tab_buttons}
        </div>
        <div class="versions-container">
            {versions_html}
        </div>
        <div class="source-link">
            {source_link}
        </div>
    </main>
    <script src="static/js/article.js"></script>
</body>
</html>"""
    
    def _format_content(self, content: str, lang: str) -> str:
        paragraphs = content.split('\n\n')
        formatted = ""
        for p in paragraphs:
            p = p.strip()
            if p:
                formatted += f'<p class="clickable-text" data-lang="{lang}">{p}</p>\n'
        return formatted
    
    def _copy_static_assets(self):
        import shutil
        static_src = os.path.join(os.path.dirname(__file__), "..", "static")
        static_dst = os.path.join(self.output_dir, "static")
        if os.path.exists(static_dst):
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = SiteGenerator()
    generator.generate()