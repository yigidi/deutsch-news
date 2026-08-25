import json
import logging
import os
import requests
from typing import Dict, List, Optional, Callable
from backend.config import (
    CEFR_LEVELS, AI_PROVIDER,
    OLLAMA_MODEL, OLLAMA_HOST,
    GROQ_API_KEY, GROQ_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_MODEL,
    HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL
)

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.provider = AI_PROVIDER
        self._init_provider_chain()
    
def _init_provider_chain(self):
        """Build a chain of providers to try in order"""
        self.providers = []
        self.ollama_client = None
        
        # Detect if running in CI (no local Ollama)
        in_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
        
        # Primary provider from config
        primary_added = False
        if self.provider == "groq" and GROQ_API_KEY:
            self.providers.append(("groq", self._call_groq, GROQ_MODEL))
            primary_added = True
        elif self.provider == "openrouter" and OPENROUTER_API_KEY:
            self.providers.append(("openrouter", self._call_openrouter, OPENROUTER_MODEL))
            primary_added = True
        elif self.provider == "huggingface" and HUGGINGFACE_API_KEY:
            self.providers.append(("huggingface", self._call_huggingface, HUGGINGFACE_MODEL))
            primary_added = True
        
        # If no primary configured, try any available API
        if not primary_added:
            if GROQ_API_KEY:
                self.providers.append(("groq", self._call_groq, GROQ_MODEL))
            if OPENROUTER_API_KEY:
                self.providers.append(("openrouter", self._call_openrouter, OPENROUTER_MODEL))
            if HUGGINGFACE_API_KEY:
                self.providers.append(("huggingface", self._call_huggingface, HUGGINGFACE_MODEL))
        
        # Add fallbacks (if not already primary)
        if self.provider != "groq" and GROQ_API_KEY:
            self.providers.append(("groq", self._call_groq, GROQ_MODEL))
        if self.provider != "openrouter" and OPENROUTER_API_KEY:
            self.providers.append(("openrouter", self._call_openrouter, OPENROUTER_MODEL))
        if self.provider != "huggingface" and HUGGINGFACE_API_KEY:
            self.providers.append(("huggingface", self._call_huggingface, HUGGINGFACE_MODEL))
        if self.provider != "ollama" and not in_ci:
            import ollama
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)
            self.providers.append(("ollama", self._call_ollama, OLLAMA_MODEL))
        
        # DEBUG: Store provider chain for HTML display
        self._provider_chain_debug = [f"{p[0]}({p[2]})" for p in self.providers]
        logger.info(f"Provider chain: {self._provider_chain_debug}")
        if not self.providers:
            logger.error("NO AI PROVIDERS AVAILABLE! Set GROQ_API_KEY, OPENROUTER_API_KEY, or HUGGINGFACE_API_KEY")
    
    def _call_with_fallback(self, prompt: str, temperature: float = 0.3) -> str:
        """Try each provider in chain until one works"""
        last_error = None
        
        for name, call_func, model in self.providers:
            try:
                logger.info(f"Trying provider: {name} (model: {model})")
                result = call_func(prompt, temperature)
                logger.info(f"Provider {name} succeeded")
                return result
            except Exception as e:
                logger.warning(f"Provider {name} failed: {type(e).__name__}: {e}")
                last_error = e
                continue
        
        logger.error(f"ALL PROVIDERS FAILED. Last error: {last_error}")
        raise last_error or Exception("All providers failed")
    
    def process_article(self, article: Dict) -> Dict:
        original_lang = article.get("original_language", "unknown")
        content = article.get("content", "")
        title = article.get("title", "")
        
        if original_lang == "de":
            levels = CEFR_LEVELS["de"]
            processed = self._process_german(content, title, levels)
        else:
            german_translation = self._translate_to_german(content, title, original_lang)
            german_content = german_translation.get("content", content)
            german_title = german_translation.get("title", title)
            
            levels = CEFR_LEVELS["de"]
            processed = self._process_german(german_content, german_title, levels)
            
            processed["Original"] = {"title": title, "content": content, "language": original_lang}
        
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
    
    def _simplify_to_level(self, content: str, title: str, level: str) -> Dict:
        prompt = self._build_simplification_prompt(content, title, level)
        logger.info(f"Simplifying to {level}, content length: {len(content)}")
        
        try:
            response = self._call_with_fallback(prompt, temperature=0.3)
            logger.info(f"Raw response for {level}: {response[:200]}")
            result = json.loads(response)
            simplified_content = result.get("content", content)
            simplified_title = result.get("title", title)
            
            if simplified_content == content and level != "Original":
                logger.warning(f"AI returned same content for {level}, simplification may have failed")
            
            return {
                "title": simplified_title,
                "content": simplified_content
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {level}: {e}, response: {response[:500]}")
            return {"title": title, "content": content, "_ai_error": f"JSON parse error: {e}"}
        except Exception as e:
            logger.error(f"Error simplifying to {level}: {e}")
            return {"title": title, "content": content, "_ai_error": str(e)}
    
    def _translate_to_german(self, content: str, title: str, source_lang: str) -> Dict:
        prompt = f"""Translate the following news article from {source_lang} to German (C1 level).
Keep the meaning accurate but use sophisticated German vocabulary and grammar appropriate for C1 level.

Title: {title}
Content: {content}

Return JSON with keys: title, content"""
        
        try:
            response = self._call_with_fallback(prompt, temperature=0.2)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error translating: {e}")
            return {"title": title, "content": content}
    
    def _call_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        if not self.ollama_client:
            import ollama
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)
        response = self.ollama_client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            format="json",
            options={"temperature": temperature}
        )
        return response["response"]
    
    def _call_groq(self, prompt: str, temperature: float = 0.3) -> str:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        logger.info(f"Calling Groq API with model: {GROQ_MODEL}")
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=data, timeout=60
        )
        if response.status_code != 200:
            logger.error(f"Groq API error {response.status_code}: {response.text}")
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info(f"Groq response received, length: {len(content)}")
        return content
    
    def _call_openrouter(self, prompt: str, temperature: float = 0.3) -> str:
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set")
        logger.info(f"Calling OpenRouter API with model: {OPENROUTER_MODEL}")
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yigidi/deutsch-news",
            "X-Title": "Deutsch News"
        }
        data = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=data, timeout=60
        )
        if response.status_code != 200:
            logger.error(f"OpenRouter API error {response.status_code}: {response.text}")
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info(f"OpenRouter response received, length: {len(content)}")
        return content
    
    def _call_huggingface(self, prompt: str, temperature: float = 0.3) -> str:
        if not HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY not set")
        logger.info(f"Calling HuggingFace API with model: {HUGGINGFACE_MODEL}")
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": prompt,
            "parameters": {"temperature": temperature, "max_new_tokens": 2000}
        }
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}",
            headers=headers, json=data, timeout=120
        )
        if response.status_code != 200:
            logger.error(f"HuggingFace API error {response.status_code}: {response.text}")
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list):
            content = result[0].get("generated_text", "")
        else:
            content = result.get("generated_text", "")
        logger.info(f"HuggingFace response received, length: {len(content)}")
        return content
    
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