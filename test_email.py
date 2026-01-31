#!/usr/bin/env python3
"""
Test script to verify email delivery functionality
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
from email_delivery import send_email
from models import NewsArticle

# Email Settings
load_dotenv()
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST")
EMAIL_SMTP_PORT = os.getenv("EMAIL_SMTP_PORT")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

#from config import EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENT

def test_email_config():
    """Test if email configuration is properly loaded"""
    print("Testing email configuration...")
    print(f"SMTP Host: {EMAIL_SMTP_HOST}")
    print(f"SMTP Port: {EMAIL_SMTP_PORT}")
    print(f"Username: {EMAIL_USERNAME}")
    print(f"Recipient: {EMAIL_RECIPIENT}")
    
    # Check if credentials are properly set
    if not EMAIL_USERNAME or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        print("ERROR: Email credentials not properly configured!")
        return False
    else:
        print("Email credentials appear to be properly configured")
        return True

def test_email_function():
    """Test the email sending function with a dummy article"""
    print("\nTesting email function with dummy article...")
    
    # Create a dummy article for testing
    dummy_article = NewsArticle(
        title="Test Article",
        url="https://example.com/test",
        content="This is a test article content for email delivery testing.",
        summary="This is a test summary for email delivery testing.",
        source="test",
        timestamp="2026-01-06T19:00:00Z",
        language="en",
        topic="test",
        metadata={}
    )
    
    articles = [dummy_article]
    
    try:
        result = send_email(articles)
        if result:
            print("SUCCESS: Email sent successfully!")
        else:
            print("FAILED: Email sending failed")
        return result
    except Exception as e:
        print(f"ERROR during email sending: {e}")
        return False

if __name__ == "__main__":
    print("=== Email Delivery Test ===")
    
    # Test configuration
    config_ok = test_email_config()
    
    if config_ok:
        # Test function
        test_email_function()
    else:
        print("Cannot test email function due to configuration issues")