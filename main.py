#!/usr/bin/env python3
"""
Main entry point for the News Agent system
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from news_fetcher import NewsFetcher
from scheduler import main as scheduler_main

def main():
    """Main function to run the News Agent"""
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
    
    # Check if running as scheduler or manual execution
    if len(sys.argv) > 1 and sys.argv[1] == "schedule":
        # Run scheduled execution
        scheduler_main()
    else:
        # Run manual execution
        logger.info("Starting manual News Agent execution")
        
        try:
            fetcher = NewsFetcher()
            articles = fetcher.fetch_and_process()
            
            if articles:
                logger.info(f"Successfully processed {len(articles)} articles")
            else:
                logger.warning("No articles were processed")
                
        except Exception as e:
            logger.error(f"Error in manual execution: {e}")
            raise

if __name__ == "__main__":
    main()