import os
import logging
from gtts import gTTS
from typing import Dict, Optional
from backend.config import AUDIO_DIR

logger = logging.getLogger(__name__)

class TTSGenerator:
    def __init__(self):
        os.makedirs(AUDIO_DIR, exist_ok=True)
    
    def generate_audio(self, text: str, article_id: str, level: str) -> Optional[str]:
        filename = f"{article_id}_{level}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        if os.path.exists(filepath):
            logger.info(f"Audio already exists: {filepath}")
            return f"static/audio/{filename}"
        
        try:
            tts = gTTS(text=text[:5000], lang='de', slow=False)
            tts.save(filepath)
            logger.info(f"Generated audio: {filepath}")
            return f"static/audio/{filename}"
        except Exception as e:
            logger.error(f"Error generating audio with gTTS: {e}")
            return None
    
    def generate_for_article(self, article: Dict) -> Dict:
        versions = article.get("versions", {})
        audio_map = {}
        
        for level, version in versions.items():
            if level != "Original" or article.get("original_language") == "de":
                content = version.get("content", "")
                if content:
                    audio_path = self.generate_audio(content, article["id"], level)
                    if audio_path:
                        audio_map[level] = audio_path
        
        return audio_map


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tts = TTSGenerator()
    path = tts.generate_audio("Hallo, dies ist ein Test auf Deutsch.", "test_123", "A1")
    print(f"Audio: {path}")