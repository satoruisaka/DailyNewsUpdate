"""
Data models for the News Agent system
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class NewsArticle:
    """Represents a processed news article"""
    title: str
    url: str
    content: str
    summary: str
    source: str  # 'brave' or 'duckduckgo'
    timestamp: str
    language: str
    topic: str
    image_path: Optional[str] = None
    metadata: dict = None