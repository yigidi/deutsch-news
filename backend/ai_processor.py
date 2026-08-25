import ollama
import json
import logging
from typing import Dict, List, Optional
from backend.config import OLLAMA_MODEL, OLLAMA_HOST, CEFR_LEVELS

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.client = ollama.Client(host=OLLAMA_HOST)
        self.model = OLLAMA_MODEL
    
    def process_article(self, article: Dict) -> Dict:
        original_lang = article.get("original_language", "unknown")
        content = article.get("content", "")
        title = article.get("title", "")
        
        if original_lang == "de":
            levels = CEFR_LEVELS["de"]
            processed = self._process_german(content, title, levels)
        else:
            levels = CEFR_LEVELS["other"]
            processed = self._process_foreign(content, title, original_lang, levels)
        
        article["versions"] = processed
        return article
    
    def _process_german(self, content: str, title: str, levels: List[str]) -> Dict:
        versions = {}
        
        for level in levels:
            if level == "Original":
                versions[level] = {"title": title, "content": content}
            else:
                simplified = self._simplify_to_level(content, title, level)
                versions[level] = simplified
        
        return versions
    
    def _process_foreign(self, content: str, title: str, original_lang: str, levels: List[str]) -> Dict:
        versions = {}
        
        german_translation = self._translate_to_german(content, title, original_lang)
        c1_version = self._simplify_to_level(german_translation["content"], german_translation["title"], "C1")
        
        versions["C1"] = c1_version
        versions["Original"] = {"title": title, "content": content, "language": original_lang}
        
        return versions
    
    def _simplify_to_level(self, content: str, title: str, level: str) -> Dict:
        prompt = self._build_simplification_prompt(content, title, level)
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                format="json",
                options={"temperature": 0.3}
            )
            result = json.loads(response["response"])
            return {
                "title": result.get("title", title),
                "content": result.get("content", content)
            }
        except Exception as e:
            logger.error(f"Error simplifying to {level}: {e}")
            return {"title": title, "content": content}
    
    def _translate_to_german(self, content: str, title: str, source_lang: str) -> Dict:
        prompt = f"""Translate the following news article from {source_lang} to German (C1 level).
Keep the meaning accurate but use sophisticated German vocabulary and grammar appropriate for C1 level.

Title: {title}
Content: {content}

Return JSON with keys: title, content"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                format="json",
                options={"temperature": 0.2}
            )
            return json.loads(response["response"])
        except Exception as e:
            logger.error(f"Error translating: {e}")
            return {"title": title, "content": content}
    
    def _build_simplification_prompt(self, content: str, title: str, level: str) -> str:
        level_descriptions = {
            "A1": "Very simple German, present tense only, short sentences (max 10 words), basic vocabulary (A1 level), no subordinate clauses",
            "A2": "Simple German, present and perfect tense, short sentences (max 15 words), everyday vocabulary (A2 level), simple subordinate clauses with 'weil', 'dass'",
            "B1": "Standard German, various tenses, medium sentences (max 20 words), broader vocabulary (B1 level), subordinate clauses, passive voice occasionally",
            "B2": "Advanced German, complex sentence structures, varied vocabulary (B2 level), idiomatic expressions, all tenses, nuanced expressions",
            "C1": "Sophisticated German, complex syntax, academic/formal vocabulary (C1 level), nuanced expressions, implicit meanings, stylistic devices"
        }
        
        desc = level_descriptions.get(level, level_descriptions["B1"])
        
        return f"""Rewrite the following German news article for {level} level learners.

Level requirements: {desc}

Original title: {title}
Original content: {content}

Return ONLY valid JSON with keys: title, content
- title: simplified title
- content: simplified article text (3-5 paragraphs)
- Do not add explanations, only the JSON"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    processor = AIProcessor()
    
    test_article = {
        "title": "Bundeskanzler besucht Frankreich",
        "content": "Bundeskanzler Olaf Scholz hat Frankreich besucht, um über die europäische Sicherheitsarchitektur zu sprechen. Bei dem Treffen mit Präsident Macron ging es um die Stärkung der deutsch-französischen Zusammenarbeit.",
        "original_language": "de"
    }
    
    result = processor.process_article(test_article)
    print(json.dumps(result["versions"], indent=2, ensure_ascii=False))