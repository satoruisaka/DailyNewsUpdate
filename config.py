"""
Configuration settings for the automated news delivery system.
This file defines topics to track, email settings, and processing parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "news_articles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# News Topics
NEWS_TOPICS = [
    "Latest news on CES 2026",
    "日本のニュース速報",
    "Noticias nacionales de última hora",
    "أخبار محلية عاجلة",
    "国内突发新闻"
]

# Processing Parameters
MAX_SUMMARY_WORDS = 100
MAX_ARTICLE_CHARS = 10000
NUM_RESULTS_PER_TOPIC = 5

# Translation Settings
ENABLE_TRANSLATION = True
TRANSLATION_MODEL = "ministral-3:14b"
LLM_TIMEOUT = 300  # seconds - timeout for Ollama API calls (summarization, translation)

# Image Generation Settings
ENABLE_IMAGE_GENERATION = True
TWISTEDPIC_URL = os.getenv("TWISTEDPIC_URL", "http://localhost:5000")
IMAGE_RESOLUTION = "landscape"  # landscape (1024x768), portrait (768x1024), square (1024x1024)
IMAGE_STEPS = 28  # SD3 optimal (20-28 for faster, 28-40 for quality)
IMAGE_CFG = 4.5   # SD3 optimal guidance scale

# Web Search Settings (Brave API)
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
if not BRAVE_API_KEY:
    print("⚠️  WARNING: BRAVE_API_KEY not set in .env file")
    print("   Web search will fail. Add BRAVE_API_KEY to .env file.")

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
WEB_FETCH_TIMEOUT = 10  # seconds
WEB_FETCH_MAX_CHARS = 10000  # per URL

# User-Agent rotation to avoid bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]


# Scheduling
FETCH_INTERVAL_HOURS = 24

# MRA Integration
MRA_DATA_DIR = Path("../MRA/data")
MRA_WEB_CACHE_DIR = MRA_DATA_DIR / "web_cache"
MRA_MARKDOWN_DIR = MRA_DATA_DIR / "markdown" / "news_articles"

# Create MRA directories if they don't exist
MRA_WEB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MRA_MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)