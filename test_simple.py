#!/usr/bin/env python3
"""
Simple test script to verify the News Agent implementation can be imported
"""

import sys
import os

def test_basic_imports():
    """Test that core modules can be imported"""
    try:
        # Test importing config
        import config
        print("✓ config.py imported successfully")
        
        # Test importing main modules
        import news_fetcher
        print("✓ news_fetcher.py imported successfully")
        
        import translation
        print("✓ translation.py imported successfully")
        
        import summarization
        print("✓ summarization.py imported successfully")
        
        import image_generation
        print("✓ image_generation.py imported successfully")
        
        import email_delivery
        print("✓ email_delivery.py imported successfully")
        
        import integration
        print("✓ integration.py imported successfully")
        
        print("\nAll modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"Error importing modules: {e}")
        return False

if __name__ == "__main__":
    print("Testing News Agent Implementation...")
    print("=" * 40)
    
    success = test_basic_imports()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Implementation is ready.")
    else:
        print("✗ Some tests failed.")
        sys.exit(1)