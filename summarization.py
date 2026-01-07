"""
Summarization Module
This module provides summarization functionality for news articles, condensing content to under 500 words.
"""

import os
import requests
import logging
from typing import Optional
from models import NewsArticle
from config import TRANSLATION_MODEL, MAX_SUMMARY_WORDS, LLM_TIMEOUT

logger = logging.getLogger(__name__)

def summarize_article(article: NewsArticle) -> NewsArticle:
    """
    Summarize article content to under MAX_SUMMARY_WORDS words using Ollama LLM
    """
    # Check if we have content to summarize
    if not article.content or len(article.content.strip()) == 0:
        logger.warning(f"No content to summarize for article '{article.title}'")
        return article
    
    # Check if content is too short
    if len(article.content.strip()) < 10:
        logger.warning(f"Article content too short to summarize for '{article.title}'")
        return article
    
    # Create summarization prompt
    prompt = f"""
Please summarize the following article in {MAX_SUMMARY_WORDS} words or less.
Focus on the key points and main ideas.
Do not include any explanations or comments.

Article:
{article.content}
"""

    logger.info(f"Attempting to summarize article: {article.title}")
    logger.debug(f"Article content length: {len(article.content)}")
    logger.debug(f"Prompt length: {len(prompt)}")
    logger.debug(f"Using model: {TRANSLATION_MODEL}")

    try:
        # Send to Ollama LLM
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": TRANSLATION_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=LLM_TIMEOUT
        )
        
        logger.info(f"Ollama response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"Ollama response JSON: {result}")
            summary = result.get("response", "").strip()
            
            logger.info(f"Summary extracted: {summary[:100]}. ..")
            
            if summary:
                article.summary = summary
                logger.info("Summary successfully set")
            else:
                logger.warning("Received empty summary from LLM")
                article.summary = "Summarization failed - no content returned from LLM"
                
        else:
            logger.warning(f"Summarization failed for article '{article.title}': {response.status_code}")
            logger.debug(f"Response text: {response.text}")
            article.summary = f"Summarization failed - HTTP {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error summarizing article '{article.title}': {e}")
        logger.exception("Full traceback")
        article.summary = f"Summarization failed - {str(e)}"
        # Keep original content if summarization fails
        
    return article