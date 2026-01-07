"""
MRA Integration Module
This module provides integration with MRA's existing data directory structure.
"""

import os
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from models import NewsArticle
from config import MRA_MARKDOWN_DIR

logger = logging.getLogger(__name__)

def save_article_to_mra(article: NewsArticle) -> bool:
    """
    Save article to MRA's data directory as markdown
    """
    try:
        # Create filename based on timestamp and title
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        title_part = article.title[:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{timestamp}_{title_part}.md"
        
        # Full path to save the article
        file_path = MRA_MARKDOWN_DIR / filename
        
        # Create markdown content
        content = f"""# {article.title}

**Source:** [{article.url}]({article.url})

**Topic:** {article.topic}

**Published:** {article.timestamp}

**Language:** {article.language}

## Summary
{article.summary}

## Full Content
{article.content}

"""
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Saved article to MRA: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving article to MRA: {e}")
        return False

def get_article_hash(article: NewsArticle) -> str:
    """
    Generate a hash for the article content to detect duplicates
    """
    content = f"{article.title}{article.url}{article.content}"
    return hashlib.md5(content.encode()).hexdigest()