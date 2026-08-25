import json
import logging
from typing import Dict, Optional
from deep_translator import GoogleTranslator
from backend.config import DATA_DIR

logger = logging.getLogger(__name__)

class WordTranslator:
    def __init__(self):
        self.cache_file = os.path.join(DATA_DIR, "translation_cache.json")
        self.cache = self._load_cache()
        self.translator = GoogleTranslator(source='de', target='tr')
    
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def translate_word(self, word: str) -> Dict:
        clean_word = word.lower().strip('.,!?;:()[]{}"\''"")
        
        if clean_word in self.cache:
            return self.cache[clean_word]
        
        try:
            translation = self.translator.translate(clean_word)
            result = {
                "word": clean_word,
                "translation": translation,
                "examples": self._get_examples(clean_word)
            }
            self.cache[clean_word] = result
            self._save_cache()
            return result
        except Exception as e:
            logger.error(f"Translation error for '{word}': {e}")
            return {"word": clean_word, "translation": "Çeviri yapılamadı", "examples": []}
    
    def _get_examples(self, word: str) -> list:
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    translator = WordTranslator()
    result = translator.translate_word("Bundeskanzler")
    print(json.dumps(result, ensure_ascii=False, indent=2))