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

# News Topics (Mainland Chinese, Russian, Arabic, Hebrew, Spanish)
NEWS_TOPICS = [
    "每日新闻 今日头条",
    "Новости на сегодня свежие",
    "أخبار يومية اليوم",
    "היום חדשות יומיות",
    "Noticias diarias hoy"
]

# Processing Parameters
MAX_SUMMARY_WORDS = 100
MAX_ARTICLE_CHARS = 10000
NUM_RESULTS_PER_TOPIC = 5

# Translation Settings
ENABLE_TRANSLATION = True
TRANSLATION_MODEL = "ministral-3:14b"
LLM_TIMEOUT = 300  # seconds - timeout for Ollama API calls (summarization, translation)

# Ollama GPU Memory Management
# NOTE: Ollama keeps LLM models in GPU memory by default (5 minute timeout).
# This conflicts with TwistedPic's SDXL which needs GPU memory for image generation.
# Setting keep_alive="0" unloads model immediately after request to free GPU memory.
# See: https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-keep-a-model-loaded-in-memory
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "0")  # "0" = unload immediately after use

# Image Generation Settings
ENABLE_IMAGE_GENERATION = True
TWISTEDPIC_URL = os.getenv("TWISTEDPIC_URL", "http://localhost:5000")
IMAGE_MODEL = "sd3_large"  # Options: sd3_large, sdxl_base
IMAGE_RESOLUTION = "landscapesm"  # landscape (1024x768), portrait (768x1024), square (1024x1024)
IMAGE_STEPS = 25  # SD3 optimal (20-28 for faster, 28-40 for quality)
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

# Security and Anti-Blocking Settings
MANUAL_REDIRECT_HANDLING = True  # Manually handle redirects to validate domains
MAX_REDIRECTS = 3  # Maximum number of redirects to follow
REDIRECT_TIMEOUT = 5  # Timeout for each redirect attempt (seconds)

# Allowed domains for redirects (whitelist approach)
# Only follow redirects to these known news domains
ALLOWED_REDIRECT_DOMAINS = [
    'xinhuanet.com', 'cctv.com', 'thepaper.cn', 'caixin.com', 'chinadaily.com.cn',
    'tass.ru', 'ria.ru', 'kommersant.ru', 'rbc.ru',
    'haaretz.co.il', 'ynet.co.il', 'israelhayom.co.il', 'kan.org.il',
    'aljazeera.net', 'alarabiya.net', 'asharq.com', 'ahram.org.eg',
    'elpais.com', 'elmundo.es', 'clarin.com'
]

# Blocked domains (known tracking/ad networks)
BLOCKED_DOMAINS = [
    'yahoo.com', 'yimg.com', 'yahooapis.com',
    'doubleclick.net', 'google-analytics.com', 'googletagmanager.com',
    'facebook.com', 'fbcdn.net', 'facebook.net',
    'twitter.com', 'twimg.com',
    'scorecardresearch.com', 'quantserve.com'
]

# Request delays to avoid rate limiting
REQUEST_DELAY_MIN = 2  # Minimum seconds between requests
REQUEST_DELAY_MAX = 4  # Maximum seconds between requests (randomized)
SOURCE_DELAY = 3  # Seconds to wait between different news sources

# Scheduling
FETCH_INTERVAL_HOURS = 24

# MRA Integration
MRA_DATA_DIR = Path("../MRA/data")
MRA_WEB_CACHE_DIR = MRA_DATA_DIR / "web_cache"
MRA_MARKDOWN_DIR = MRA_DATA_DIR / "markdown" / "news_articles"

# Create MRA directories if they don't exist
MRA_WEB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MRA_MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)