"""
News Fetcher Module
This module handles the core functionality of fetching news articles, processing them
(translation, summarization), and preparing them for delivery and storage.

Modified to fetch news directly from specific international news websites:
- Mainland Chinese (Xinhua, CCTV, The Paper, Caixin, China Daily)
- Russian (TASS, RIA, Kommersant, RBC)
- Hebrew (Haaretz, Ynet, Israel Hayom, Kan)
- Arabic (Al Jazeera, Al Arabiya, Asharq, Al-Ahram)
- Spanish (El País, El Mundo, Clarín)
"""

import os
import time
import requests
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from urllib.parse import quote, urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Import configuration
from config import (
    NEWS_TOPICS,
    NUM_RESULTS_PER_TOPIC,
    MRA_WEB_CACHE_DIR,
    MRA_MARKDOWN_DIR,
    ENABLE_TRANSLATION,
    TRANSLATION_MODEL,
    ENABLE_IMAGE_GENERATION,
    TWISTEDPIC_URL,
    MAX_ARTICLE_CHARS,
    WEB_FETCH_TIMEOUT,
    USER_AGENTS,
    MANUAL_REDIRECT_HANDLING,
    MAX_REDIRECTS,
    REDIRECT_TIMEOUT,
    ALLOWED_REDIRECT_DOMAINS,
    BLOCKED_DOMAINS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    SOURCE_DELAY
)

# Import data models
from models import NewsArticle

# Import other modules
from translation import translate_article
from summarization import summarize_article
from image_generation import generate_article_image
from email_delivery import send_email
from integration import save_article_to_mra

# News Website Sources Configuration
NEWS_SOURCES = {
    'chinese': [
        {'name': 'Xinhua', 'url': 'https://www.xinhuanet.com', 'lang': 'zh'},
        {'name': 'CCTV', 'url': 'https://news.cctv.com', 'lang': 'zh'},
        {'name': 'The Paper', 'url': 'https://www.thepaper.cn', 'lang': 'zh'},
        {'name': 'Caixin', 'url': 'https://www.caixin.com', 'lang': 'zh'},
        {'name': 'China Daily', 'url': 'https://cn.chinadaily.com.cn', 'lang': 'zh'}
    ],
    'russian': [
        {'name': 'TASS', 'url': 'https://tass.ru', 'lang': 'ru'},
        {'name': 'RIA', 'url': 'https://ria.ru', 'lang': 'ru'},
        {'name': 'Kommersant', 'url': 'https://www.kommersant.ru', 'lang': 'ru'},
        {'name': 'RBC', 'url': 'https://www.rbc.ru', 'lang': 'ru'}
    ],
    'hebrew': [
        {'name': 'Haaretz', 'url': 'https://www.haaretz.co.il', 'lang': 'he'},
        {'name': 'Ynet', 'url': 'https://www.ynet.co.il', 'lang': 'he'},
        {'name': 'Israel Hayom', 'url': 'https://www.israelhayom.co.il', 'lang': 'he'},
        {'name': 'Kan News', 'url': 'https://www.kan.org.il', 'lang': 'he'}
    ],
    'arabic': [
        {'name': 'Al Jazeera', 'url': 'https://www.aljazeera.net', 'lang': 'ar'},
        {'name': 'Al Arabiya', 'url': 'https://www.alarabiya.net', 'lang': 'ar'},
        {'name': 'Asharq', 'url': 'https://www.asharq.com', 'lang': 'ar'}
#        {'name': 'Al-Ahram', 'url': 'https://gate.ahram.org.eg', 'lang': 'ar'},
    ],
    'spanish': [
        {'name': 'El País', 'url': 'https://elpais.com', 'lang': 'es'},
#        {'name': 'El Mundo', 'url': 'https://elmundo.es', 'lang': 'es'},
        {'name': 'Clarín', 'url': 'https://clarin.com', 'lang': 'es'}
    ]
}

class NewsFetcher:
    """Main class for fetching and processing news articles from international news sources"""
    
    def __init__(self):
        # Use isolated sessions per domain to prevent cross-site tracking
        self.sessions = {}  # Will create session per domain
        self.logger = logging.getLogger(__name__)
        self.sources = NEWS_SOURCES
        
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool."""
        return random.choice(USER_AGENTS)
    
    def _get_session(self, domain: str) -> requests.Session:
        """Get or create an isolated session for a specific domain.
        This prevents cross-site tracking and cookie sharing.
        """
        if domain not in self.sessions:
            session = requests.Session()
            # Strict headers - no image/media acceptance
            session.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',  # NO images
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',  # Do Not Track
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            self.sessions[domain] = session
            self.logger.debug(f"Created isolated session for domain: {domain}")
        return self.sessions[domain]
    
    def _is_domain_blocked(self, url: str) -> bool:
        """Check if URL domain is in blocked list (tracking/ad networks)."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            return any(blocked in domain for blocked in BLOCKED_DOMAINS)
        except:
            return False
    
    def _is_redirect_allowed(self, url: str) -> bool:
        """Check if redirect URL is in allowed domains list."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            return any(allowed in domain for allowed in ALLOWED_REDIRECT_DOMAINS)
        except:
            return False
    
    def _handle_redirects_manually(self, url: str, session: requests.Session, headers: dict) -> Optional[requests.Response]:
        """Manually handle redirects with domain validation to prevent tracking.
        Only follows redirects to whitelisted domains.
        """
        redirect_count = 0
        current_url = url
        
        while redirect_count < MAX_REDIRECTS:
            try:
                # Check if URL is blocked
                if self._is_domain_blocked(current_url):
                    self.logger.warning(f"Blocked redirect to tracking domain: {current_url}")
                    return None
                
                # Make request with redirects disabled
                response = session.get(
                    current_url,
                    headers=headers,
                    timeout=REDIRECT_TIMEOUT,
                    allow_redirects=False  # Handle manually
                )
                
                # Check if this is a redirect
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_url = response.headers.get('Location')
                    if not redirect_url:
                        self.logger.warning(f"Redirect without Location header: {current_url}")
                        return response
                    
                    # Make redirect URL absolute
                    if not redirect_url.startswith('http'):
                        redirect_url = urljoin(current_url, redirect_url)
                    
                    # Validate redirect domain
                    if not self._is_redirect_allowed(redirect_url):
                        self.logger.warning(f"Redirect to non-whitelisted domain blocked: {redirect_url}")
                        return response  # Return original response instead of following
                    
                    self.logger.debug(f"Following redirect [{redirect_count + 1}/{MAX_REDIRECTS}]: {redirect_url}")
                    current_url = redirect_url
                    redirect_count += 1
                else:
                    # Not a redirect, return the response
                    return response
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout following redirect: {current_url}")
                return None
            except Exception as e:
                self.logger.warning(f"Error following redirect: {e}")
                return None
        
        self.logger.warning(f"Max redirects ({MAX_REDIRECTS}) exceeded for {url}")
        return None
    
    def fetch_articles(self) -> List[NewsArticle]:
        """Fetches articles from all configured news sources"""
        articles = []
        
        # Fetch from all language categories
        for lang_category, sources in self.sources.items():
            self.logger.info(f"Fetching articles from {lang_category} sources...")
            for source in sources:
                self.logger.info(f"  - {source['name']} ({source['url']})")
                source_articles = self._fetch_from_source(source)
                articles.extend(source_articles)
                # Randomized delay between sources to avoid rate limiting
                delay = random.uniform(REQUEST_DELAY_MIN, SOURCE_DELAY)
                self.logger.debug(f"Waiting {delay:.1f}s before next source...")
                time.sleep(delay)
        
        self.logger.info(f"Total articles fetched: {len(articles)}")
        return articles
    
    def _fetch_from_source(self, source: Dict[str, str]) -> List[NewsArticle]:
        """Fetch articles from a specific news source"""
        articles = []
        
        try:
            # Get isolated session for this domain
            parsed = urlparse(source['url'])
            domain = parsed.netloc.replace('www.', '')
            session = self._get_session(domain)
            
            # Secure headers - no Referer, no image acceptance
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Referer': source['url']  # Only send referer to same domain
            }
            
            # Fetch the homepage with manual redirect handling if enabled
            if MANUAL_REDIRECT_HANDLING:
                response = self._handle_redirects_manually(source['url'], session, headers)
                if not response:
                    self.logger.error(f"Failed to fetch {source['name']} - redirect blocked or failed")
                    return articles
            else:
                response = session.get(
                    source['url'],
                    headers=headers,
                    timeout=WEB_FETCH_TIMEOUT,
                    allow_redirects=True
                )
            
            response.raise_for_status()
            
            # Parse the page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article links
            article_links = self._extract_article_links(soup, source)
            
            # Limit to NUM_RESULTS_PER_TOPIC articles per source
            article_links = article_links[:NUM_RESULTS_PER_TOPIC]
            
            self.logger.info(f"    Found {len(article_links)} article links from {source['name']}")
            
            # Fetch each article
            for link_url, link_title in article_links:
                try:
                    # Make URL absolute if needed
                    if not link_url.startswith('http'):
                        link_url = urljoin(source['url'], link_url)
                    
                    # Fetch article content with domain session
                    content = self._fetch_article_content(link_url, domain, session)
                    
                    if content and len(content) > 100:
                        article = NewsArticle(
                            title=link_title or "No title",
                            url=link_url,
                            content=content,
                            summary="",  # Will be generated during processing
                            source=source['name'],
                            timestamp=datetime.now().isoformat(),
                            language=source['lang'],
                            topic=f"{source['name']} news",
                            metadata={'source_url': source['url'], 'lang_code': source['lang']}
                        )
                        articles.append(article)
                        self.logger.info(f"      ✓ Fetched: {link_title[:60]}...")
                    
                    # Randomized delay between articles to avoid rate limiting
                    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                    time.sleep(delay)
                    
                except Exception as e:
                    self.logger.warning(f"      ✗ Failed to fetch article {link_url}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"    Error fetching from {source['name']}: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup, source: Dict[str, str]) -> List[Tuple[str, str]]:
        """Extract article links from a news homepage
        Returns list of (url, title) tuples
        """
        links = []
        
        # Common selectors for news article links
        # Most news sites use <a> tags with specific classes/ids
        selectors = [
            'a[href*="/news/"]',
            'a[href*="/article/"]',
            'a[href*="/story/"]',
            'article a',
            '.article a',
            '.news a',
            '.post a',
            '[class*="article"] a',
            '[class*="news"] a',
            'main a',
            'a[href*="/20"]',  # Many news URLs contain year in path
            'a[href*="/content/"]',
            'a[href*="/politics/"]',
            'a[href*="/world/"]',
            'a[href*="/national/"]',
        ]
        
        found_links = set()
        
        # Try each selector
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href', '')
                    title = elem.get_text(strip=True)
                    
                    # Skip if no href or title
                    if not href or not title:
                        continue
                    
                    # Skip if too short (probably navigation)
                    if len(title) < 10:
                        continue
                    
                    # Skip if looks like navigation/menu
                    skip_keywords = ['menu', 'login', 'subscribe', 'cookie', 'privacy', 
                                   'contact', 'about', 'search', 'home', 'archive', 
                                   'category', 'tag', 'comment']
                    if any(kw in href.lower() for kw in skip_keywords):
                        continue
                    
                    # Make URL absolute
                    if not href.startswith('http'):
                        href = urljoin(source['url'], href)
                    
                    # Skip if not from same domain
                    if not self._is_same_domain(href, source['url']):
                        continue
                    
                    # Add if not already found
                    if href not in found_links and len(title) > 10:
                        found_links.add(href)
                        links.append((href, title))
                        
                        # Stop if we have enough
                        if len(links) >= NUM_RESULTS_PER_TOPIC * 2:
                            break
                
                if len(links) >= NUM_RESULTS_PER_TOPIC * 2:
                    break
                    
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return links
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            from urllib.parse import urlparse
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            # Remove www. for comparison
            domain1 = domain1.replace('www.', '')
            domain2 = domain2.replace('www.', '')
            return domain1 == domain2
        except:
            return False
    
    def _fetch_article_content(self, url: str, domain: str, session: requests.Session) -> str:
        """Fetch and extract article content from a URL with security measures."""
        try:
            # Secure headers - NO image/media acceptance, controlled referer
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',  # NO images/media
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',  # Do Not Track
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': f"https://{domain}"  # Only refer to same domain
            }
            
            # Check if URL is blocked before fetching
            if self._is_domain_blocked(url):
                self.logger.warning(f"Blocked article URL from tracking domain: {url}")
                return "Failed to fetch article - blocked domain"
            
            # Fetch with manual redirect handling if enabled
            if MANUAL_REDIRECT_HANDLING:
                response = self._handle_redirects_manually(url, session, headers)
                if not response:
                    self.logger.warning(f"Failed to fetch article - redirect blocked: {url}")
                    return "Failed to fetch article - redirect blocked"
            else:
                response = session.get(url, headers=headers, timeout=WEB_FETCH_TIMEOUT, allow_redirects=True)
            
            response.raise_for_status()
            
            # Log final URL for monitoring (but we've already validated it)
            self.logger.debug(f"Fetched article from: {response.url}")
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to extract main content - this varies by website
            # Common selectors for article content
            content_selectors = [
                'article',
                '[class*="article"]',
                '[class*="content"]',
                '[id*="article"]',
                '[id*="content"]',
                'main',
                '.post-content',
                '.entry-content',
                '.article-content',
                '.story-content',
                '[data-content]',
                '.post-body',
                '.article-body',
                'div[data-article]',
                'p',  # fallback to paragraphs
                'div',  # fallback to divs
                'span'  # fallback to spans
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Get text from all matching elements
                    extracted_content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    # Only use content that's substantial
                    if extracted_content and len(extracted_content) > 100:
                        content = extracted_content
                        break
            
            # If we couldn't find content with selectors, try to get text from body
            if not content:
                # Try to find the main content area more specifically
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                if main_content:
                    content = main_content.get_text(strip=True)
                else:
                    # Fallback to body content
                    body = soup.find('body')
                    if body:
                        # Try to extract meaningful text from body, excluding navigation, headers, footers
                        for element in body(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                            element.decompose()
                        content = body.get_text(strip=True)
            
            # Clean up the content
            content = ' '.join(content.split())  # Remove extra whitespace
            
            # If content is too short or looks like a redirect page, return error
            if len(content) < 200:
                # Check if it's a redirect or error page
                title = soup.find('title')
                if title and ('redirect' in title.get_text().lower() or 'error' in title.get_text().lower()):
                    self.logger.warning(f"Got redirect/error page for URL {url}")
                    return f"Failed to fetch article content - redirect or error page detected"
            
            # Limit to maximum characters
            if len(content) > MAX_ARTICLE_CHARS:
                content = content[:MAX_ARTICLE_CHARS]
            
            # If we still have very little content, return error
            if len(content) < 100:
                self.logger.warning(f"Very short content fetched from {url}")
                # Check if this is a redirect or error page by looking at title and meta tags
                title = soup.find('title')
                if title:
                    title_text = title.get_text().lower()
                    if 'redirect' in title_text or 'error' in title_text or '404' in title_text:
                        self.logger.warning(f"Detected redirect/error page for URL {url}")
                        return f"Failed to fetch article content - redirect or error page detected"
                
                # Try to get more content from the page
                # Look for specific elements that might contain article text
                text_elements = soup.find_all(['p', 'div', 'span'], limit=20)
                if text_elements:
                    additional_content = ' '.join([elem.get_text(strip=True) for elem in text_elements if elem.get_text(strip=True)])
                    if len(additional_content) > 100:
                        content = additional_content
                    else:
                        return f"Failed to fetch substantial article content from {url}"
                else:
                    return f"Failed to fetch substantial article content from {url}"
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch content from {url}: {e}")
            return f"Failed to fetch article content. Error: {e}"
    
    def process_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Process a list of articles through all steps: translation, summarization, image generation"""
        processed_articles = []
        
        for article in articles:
            try:
                self.logger.info(f"Processing article: '{article.title}'")
                
                # Translate article if needed
                if ENABLE_TRANSLATION:
                    self.logger.info("  - Translating article...")
                    article = translate_article(article)
                
                # Summarize article
                self.logger.info("  - Summarizing article...")
                article = summarize_article(article)
                
                # Generate image if enabled
                if ENABLE_IMAGE_GENERATION:
                    self.logger.info("  - Generating image...")
                    article = generate_article_image(article)
                else:
                    self.logger.info("  - Image generation disabled")
                
                # Save article to MRA
                self.logger.info("  - Saving to MRA...")
                save_article_to_mra(article)
                
                processed_articles.append(article)
                self.logger.info(f"✓ Article processing complete: '{article.title}'\n")
                
            except Exception as e:
                self.logger.error(f"Error processing article '{article.title}': {e}")
                # Continue with other articles even if one fails
                continue
                
        return processed_articles
    
    def fetch_and_process(self) -> List[NewsArticle]:
        """Fetch and process all articles in one go"""
        articles = self.fetch_articles()
        return self.process_articles(articles)