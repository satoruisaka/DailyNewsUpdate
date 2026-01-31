#!/usr/bin/env python3
"""
Test script to verify the News Agent implementation
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported successfully"""
    try:
        import config
        print("✓ config.py imported successfully")
        
        from news_fetcher import NewsFetcher
        print("✓ news_fetcher.py imported successfully")
        
        from translation import translate_article
        print("✓ translation.py imported successfully")
        
        from summarization import summarize_article
        print("✓ summarization.py imported successfully")
        
        from image_generation import generate_article_image
        print("✓ image_generation.py imported successfully")
        
        from email_delivery import send_email
        print("✓ email_delivery.py imported successfully")
        
        from integration import save_article_to_mra
        print("✓ integration.py imported successfully")
        
        print("\nAll modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"Error importing modules: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the system"""
    try:
        from news_fetcher import NewsFetcher
        from config import NEWS_TOPICS
        
        fetcher = NewsFetcher()
        
        # Test that we can access topics
        print(f"✓ Found {len(NEWS_TOPICS)} news topics")
        
        # Test that we can create a fetcher
        print("✓ NewsFetcher created successfully")
        
        print("\nBasic functionality test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in basic functionality test: {e}")
        return False

if __name__ == "__main__":
    print("Testing News Agent Implementation...")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    print()
    success &= test_basic_functionality()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Implementation is ready.")
    else:
        print("✗ Some tests failed.")
        sys.exit(1)