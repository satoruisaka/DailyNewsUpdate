#!/usr/bin/env python3
"""
Test script for the modified news_fetcher_local.py
Tests the new direct website scraping functionality
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_news_sources_config():
    """Test that NEWS_SOURCES is properly configured"""
    from news_fetcher_local import NEWS_SOURCES
    
    print("=" * 70)
    print("Testing NEWS_SOURCES Configuration")
    print("=" * 70)
    
    expected_langs = ['chinese', 'russian', 'hebrew', 'arabic', 'spanish']
    
    for lang in expected_langs:
        if lang not in NEWS_SOURCES:
            print(f"❌ Missing language category: {lang}")
            return False
        
        sources = NEWS_SOURCES[lang]
        print(f"\n{lang.upper()} sources ({len(sources)} total):")
        for source in sources:
            print(f"  ✓ {source['name']:20} | {source['url']:40} | lang: {source['lang']}")
    
    total_sources = sum(len(NEWS_SOURCES[lang]) for lang in expected_langs)
    print(f"\n✅ Total sources configured: {total_sources}")
    
    return True

def test_fetcher_initialization():
    """Test that NewsFetcher can be initialized"""
    from news_fetcher_local import NewsFetcher
    
    print("\n" + "=" * 70)
    print("Testing NewsFetcher Initialization")
    print("=" * 70)
    
    try:
        fetcher = NewsFetcher()
        print("✅ NewsFetcher initialized successfully")
        print(f"   Sources: {len(fetcher.sources)} language categories")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize NewsFetcher: {e}")
        return False

def test_method_presence():
    """Test that all required methods exist"""
    from news_fetcher_local import NewsFetcher
    
    print("\n" + "=" * 70)
    print("Testing NewsFetcher Methods")
    print("=" * 70)
    
    fetcher = NewsFetcher()
    required_methods = [
        'fetch_articles',
        '_fetch_from_source',
        '_extract_article_links',
        '_is_same_domain',
        '_fetch_article_content',
        'process_articles',
        'fetch_and_process',
        '_get_random_user_agent'
    ]
    
    all_present = True
    for method_name in required_methods:
        if hasattr(fetcher, method_name):
            print(f"  ✓ {method_name}")
        else:
            print(f"  ❌ {method_name} - MISSING!")
            all_present = False
    
    return all_present

def main():
    """Run all tests"""
    print("\n" + "🔍" * 35)
    print("News Fetcher Local - Validation Tests")
    print("🔍" * 35 + "\n")
    
    tests = [
        ("NEWS_SOURCES Configuration", test_news_sources_config),
        ("NewsFetcher Initialization", test_fetcher_initialization),
        ("Required Methods", test_method_presence),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The news fetcher is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
