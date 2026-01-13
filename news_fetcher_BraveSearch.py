"""
News Fetcher Module
This module handles the core functionality of fetching news articles, processing them
(translation, summarization), and preparing them for delivery and storage.
"""

import os
import time
import requests
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote
from bs4 import BeautifulSoup

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
    BRAVE_API_KEY,
    BRAVE_API_URL,
    WEB_FETCH_TIMEOUT,
    USER_AGENTS
)

# Import data models
from models import NewsArticle

# Import other modules
from translation import translate_article
from summarization import summarize_article
from image_generation import generate_article_image
from email_delivery import send_email
from integration import save_article_to_mra

class NewsFetcher:
    """Main class for fetching and processing news articles"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MRA-News-Agent/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.logger = logging.getLogger(__name__)
        self.brave_api_key = BRAVE_API_KEY
        
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool."""
        return random.choice(USER_AGENTS)
        
    def fetch_articles(self) -> List[NewsArticle]:
        """Fetches articles for all configured topics"""
        articles = []
        
        for topic in NEWS_TOPICS:
            self.logger.info(f"Fetching articles for topic: {topic}")
            topic_articles = self._fetch_topic_articles(topic)
            articles.extend(topic_articles)
            
        return articles
    
    def _fetch_topic_articles(self, topic: str) -> List[NewsArticle]:
        """Fetch articles for a specific topic using Brave Web Search API"""
        articles = []
        
        if not self.brave_api_key:
            self.logger.error("BRAVE_API_KEY not configured. Cannot fetch articles.")
            return articles
        
        self.logger.info(f"Searching Brave API for: '{topic}'")
        
        # Brave API headers and parameters
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.brave_api_key,
            'User-Agent': self._get_random_user_agent()
        }
        
        params = {
            'q': " " + topic,
            'count': NUM_RESULTS_PER_TOPIC,
            'text_decorations': False,
            'search_lang': 'en'
        }
        
        try:
            response = requests.get(
                BRAVE_API_URL,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Brave response
            web_results = data.get('web', {}).get('results', [])
            
            for item in web_results[:NUM_RESULTS_PER_TOPIC]:
                title = item.get('title', 'No title')
                url = item.get('url', '')
                snippet = item.get('description', '')
                
                if not url:
                    continue
                
                # Fetch the actual article content
                article_content = self._fetch_article_content(url)
                
                article = NewsArticle(
                    title=title,
                    url=url,
                    content=article_content,
                    summary=snippet,  # Use snippet as initial summary
                    source="brave",
                    timestamp=datetime.now().isoformat(),
                    language="unknown",  # Will be detected during translation
                    topic=topic,
                    metadata={'snippet': snippet}
                )
                articles.append(article)
                
                self.logger.info(f"Fetched article: {title[:50]}...")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Brave API request error for topic '{topic}': {e}")
        except Exception as e:
            self.logger.error(f"Error fetching articles for topic '{topic}': {e}")
            
        return articles
    
    def _fetch_article_content(self, url: str) -> str:
        """Fetch and extract article content from a URL"""
        try:
            # Add headers to mimic a real browser with rotating user agent
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # First, check if it's a redirect or if we can get the actual content
            response = self.session.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # If we get a redirect, check the final URL
            final_url = response.url
            self.logger.debug(f"Final URL after redirects: {final_url}")
            
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