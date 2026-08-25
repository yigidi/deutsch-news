import json
import logging
import os
import requests
import re
from typing import Dict, List, Optional
from backend.config import (
    CEFR_LEVELS, AI_PROVIDER,
    OLLAMA_MODEL, OLLAMA_HOST,
    GROQ_API_KEY, GROQ_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_MODEL,
    HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL
)

logger = logging.getLogger(__name__)

LEVEL_RULES = {
    "A1": {"max_words": 10, "tense": "present", "no_subclause": True},
    "A2": {"max_words": 15, "tense": "present_perfect", "no_subclause": True},
    "B1": {"max_words": 20, "tense": "mixed", "no_subclause": False},
    "B2": {"max_words": 30, "tense": "mixed", "no_subclause": False},
}

def simple_simplify(text: str, level: str) -> str:
    """Rule-based German simplification"""
    rules = LEVEL_RULES.get(level, LEVEL_RULES["B1"])
    max_words = rules["max_words"]
    
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    out = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        if len(words) <= max_words:
            out.append(s)
        else:
            parts = re.split(r',\s*', s)
            for p in parts:
                p = p.strip()
                if p and len(p.split()) <= max_words:
                    out.append(p + ".")
                elif p:
                    sub = ' '.join(p.split()[:max_words]) + "."
                    out.append(sub)
    return " ".join(out)

def split_paragraphs(text: str, level: str) -> str:
    simplified = simple_simplify(text, level)
    words = simplified.split()
    if len(words) <= 60:
        return simplified
    third = len(words) // 3
    p1 = " ".join(words[:third])
    p2 = " ".join(words[third:2*third])
    p3 = " ".join(words[2*third:])
    return f"{p1}.\n\n{p2}.\n\n{p3}."

class AIProcessor:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.in_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
        self.groq_model = GROQ_MODEL or "llama-3.1-8b-instant"
        self.openrouter_model = OPENROUTER_MODEL or "meta-llama/llama-3.1-8b-instruct"
        if ":free" in self.openrouter_model:
            self.openrouter_model = "meta-llama/llama-3.1-8b-instruct"
    
    def process_article(self, article: Dict) -> Dict:
        lang = article.get("original_language", "unknown")
        content = article.get("content", "")
        title = article.get("title", "")
        
        if lang == "de":
            levels = CEFR_LEVELS["de"]
            base_content, base_title = content, title
        else:
            # Translate to German first
            translated = self._translate_to_german(content, title, lang)
            base_content = translated.get("content", content)
            base_title = translated.get("title", title)
            levels = CEFR_LEVELS["de"]
        
        versions = {}
        for level in levels:
            if level == "Original":
                if lang == "de":
                    versions[level] = {"title": title, "content": content}
                else:
                    versions[level] = {"title": title, "content": content, "language": lang}
            else:
                simplified = self._simplify_to_level(base_content, base_title, level)
                versions[level] = simplified
        
        article["versions"] = versions
        return article
    
    def _simplify_to_level(self, content: str, title: str, level: str) -> Dict:
        # Try AI first
        ai_result = self._try_ai_simplify(content, title, level)
        if ai_result and ai_result.get("content") != content:
            return ai_result
        
        # Fallback to rule-based
        logger.info(f"Using rule-based fallback for {level}")
        simplified_content = split_paragraphs(content, level)
        simplified_title = simple_simplify(title, level)
        return {"title": simplified_title, "content": simplified_content}
    
    def _try_ai_simplify(self, content: str, title: str, level: str) -> Optional[Dict]:
        prompt = self._build_prompt(content, title, level)
        
        # Try Groq
        if GROQ_API_KEY:
            try:
                result = self._call_groq(prompt)
                if result:
                    return json.loads(result)
            except Exception as e:
                logger.warning(f"Groq failed: {e}")
        
        # Try OpenRouter
        if OPENROUTER_API_KEY:
            try:
                result = self._call_openrouter(prompt)
                if result:
                    return json.loads(result)
            except Exception as e:
                logger.warning(f"OpenRouter failed: {e}")
        
        return None
    
    def _translate_to_german(self, content: str, title: str, source_lang: str) -> Dict:
        prompt = f"""Translate to German (C1 level). Return JSON with title, content.

Title: {title}
Content: {content}"""
        
        # Try Groq
        if GROQ_API_KEY:
            try:
                result = self._call_groq(prompt, temp=0.2)
                return json.loads(result)
            except Exception as e:
                logger.warning(f"Translation Groq failed: {e}")
        
        # Fallback: simple translation indicator
        return {"title": f"[DE] {title}", "content": f"[Übersetzt aus {source_lang}] {content}"}
    
    def _call_groq(self, prompt: str, temp: float = 0.3) -> Optional[str]:
        if not GROQ_API_KEY:
            return None
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": self.groq_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temp,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                               headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq error: {e}")
        return None
    
    def _call_openrouter(self, prompt: str, temp: float = 0.3) -> Optional[str]:
        if not OPENROUTER_API_KEY:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yigidi/deutsch-news",
                "X-Title": "Deutsch News"
            }
            data = {
                "model": self.openrouter_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temp,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
                               headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenRouter error: {e}")
        return None
    
    def _build_prompt(self, content: str, title: str, level: str) -> str:
        rules = {
            "A1": "Sehr einfaches Deutsch, nur Präsens, kurze Sätze (max 10 Wörter), Grundwortschatz, keine Nebensätze",
            "A2": "Einfaches Deutsch, Präsens/Perfekt, kurze Sätze (max 15 Wörter), Alltagswortschatz, einfache Nebensätze mit 'weil', 'dass'",
            "B1": "Standarddeutsch, verschiedene Zeiten, mittlere Sätze (max 20 Wörter), breiterer Wortschatz, Nebensätze, gelegentlich Passiv",
            "B2": "Fortgeschrittenes Deutsch, komplexe Strukturen, variierter Wortschatz (B2), idiomatische Ausdrücke, alle Zeiten, nuancierte Ausdrücke",
        }
        desc = rules.get(level, rules["B1"])
        
        return f"""Vereinfache diesen deutschen Nachrichtentext für {level}-Lerner.

Anforderungen: {desc}

Originaltitel: {title}
Originaltext: {content}

Antworte NUR als JSON mit: title, content
- title: vereinfachter Titel
- content: vereinfachter Text (3-5 Absätze)
- Keine Erklärungen, nur JSON"""