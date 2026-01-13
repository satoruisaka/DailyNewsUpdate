"""
Translation Module
This module provides translation functionality for news articles, translating content to English when needed.
"""

import os
import requests
import logging
from typing import Optional
from models import NewsArticle
from config import TRANSLATION_MODEL, ENABLE_TRANSLATION, LLM_TIMEOUT, OLLAMA_KEEP_ALIVE

logger = logging.getLogger(__name__)

def detect_language(text: str) -> str:
    """
    Detect the language of the given text using Ollama LLM
    Returns ISO 639-1 language code (e.g., 'en', 'es', 'fr', etc.)
    """
    # Take a sample of the text to speed up detection
    sample_text = text[:500] if len(text) > 500 else text
    
    prompt = f"""
Identify the language of the following text. Respond with ONLY the ISO 639-1 language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French, etc.). Do not provide any explanation.

Text:
{sample_text}
"""
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": TRANSLATION_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": OLLAMA_KEEP_ALIVE  # Free GPU memory immediately after use
            },
            timeout=LLM_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            detected_lang = result.get("response", "").strip().lower()
            # Clean up response - take only first 2-3 chars if it's a language code
            if len(detected_lang) <= 3 and detected_lang.isalpha():
                return detected_lang
            # If response is longer, try to extract language code
            words = detected_lang.split()
            if words and len(words[0]) <= 3 and words[0].isalpha():
                return words[0]
        
        logger.warning(f"Language detection failed, defaulting to 'en'")
        return "en"
        
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        return "en"  # Default to English on error

def translate_article(article: NewsArticle) -> NewsArticle:
    """
    Translate article content to English using Ollama LLM
    """
    if not ENABLE_TRANSLATION:
        return article
    
    # Detect language if unknown
    if article.language == "unknown":
        article.language = detect_language(article.content)
    
    # Skip translation if content is already in English
    if article.language == "en":
        return article
    
    # Create translation prompt
    prompt = f"""
Translate the following text to English. Preserve the original meaning and structure.
Do not add any explanations or comments.

Text to translate:
{article.content}
"""
    
    try:
        # Send to Ollama LLM
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": TRANSLATION_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": OLLAMA_KEEP_ALIVE  # Free GPU memory immediately after use
            },
            timeout=LLM_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            translated_content = result.get("response", "").strip()
            
            if translated_content:
                article.content = translated_content
                article.language = "en"
                
        else:
            logger.warning(f"Translation failed for article '{article.title}': {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error translating article '{article.title}': {e}")
        # Keep original content if translation fails
        
    return article