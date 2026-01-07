"""
Scheduled Task Runner
This module provides a scheduled task runner for automated news delivery.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
from news_fetcher import NewsFetcher
from email_delivery import send_email
from config import FETCH_INTERVAL_HOURS

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to capture all log levels
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('newsagent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main execution function for the scheduler"""
    logger.info("Starting News Agent execution")
    
    try:
        # Initialize NewsFetcher
        fetcher = NewsFetcher()
        
        # Fetch and process articles
        logger.info("Fetching articles...")
        articles = fetcher.fetch_and_process()
        
        if articles:
            # Send email notifications
            logger.info(f"Sending email with {len(articles)} articles...")
            send_email(articles)
            
            logger.info("News Agent execution completed successfully")
        else:
            logger.warning("No articles were fetched or processed")
            
    except Exception as e:
        logger.error(f"Error in News Agent execution: {e}")
        raise

if __name__ == "__main__":
    main()