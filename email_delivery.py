"""
Email Delivery Module
This module provides email delivery functionality for news articles.
"""

import os
import smtplib
import logging
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import List
from pathlib import Path
from models import NewsArticle
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Email Settings
load_dotenv()
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST")
EMAIL_SMTP_PORT = os.getenv("EMAIL_SMTP_PORT")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

def markdown_to_html(text: str) -> str:
    """
    Convert simple markdown formatting to HTML.
    Handles: **bold**, *italic*, [links](url), line breaks, etc.
    """
    if not text:
        return ""
    
    # Escape HTML special characters first
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Convert markdown formatting
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    
    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # Links: [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    
    # Line breaks: double newlines become paragraph breaks
    paragraphs = text.split('\n\n')
    text = '</p><p>'.join(paragraphs)
    text = f'<p>{text}</p>'
    
    # Single line breaks become <br>
    text = text.replace('\n', '<br>')
    
    # Remove markdown list markers and convert to HTML lists
    text = re.sub(r'(?m)^[\*\-\+]\s+(.+?)$', r'<li>\1</li>', text)
    if '<li>' in text:
        text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    
    # Numbered lists
    text = re.sub(r'(?m)^\d+\.\s+(.+?)$', r'<li>\1</li>', text)
    
    return text

def send_email(articles: List[NewsArticle]) -> bool:
    """
    Send email notification with news articles
    """
    # The email settings are already imported from config.py, so we just need to check if they're valid
    if not EMAIL_USERNAME or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        logger.error("Email settings not configured in environment variables")
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart('related')
        msg['From'] = EMAIL_USERNAME
        msg['To'] = EMAIL_RECIPIENT
        msg['Subject'] = f"Latest News Articles - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create HTML email body with embedded images
        html_body = """
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    max-width: 800px; 
                    margin: 0 auto;
                    background-color: #f5f5f5;
                }
                .article { 
                    margin-bottom: 30px; 
                    padding: 20px; 
                    border: 1px solid #ddd; 
                    border-radius: 5px;
                    background-color: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .article-title { 
                    color: #2c3e50; 
                    font-size: 1.3em; 
                    font-weight: bold; 
                    margin-bottom: 15px;
                    line-height: 1.4;
                }
                .article-image { 
                    max-width: 100%; 
                    width: 100%; 
                    height: auto; 
                    margin: 15px 0; 
                    border-radius: 5px; 
                    display: block;
                }
                .article-summary { 
                    margin: 15px 0; 
                    color: #555; 
                    font-size: 1em;
                    line-height: 1.7;
                    text-align: justify;
                }
                .article-summary p {
                    margin: 10px 0;
                }
                .article-summary strong {
                    color: #2c3e50;
                    font-weight: 600;
                }
                .article-summary em {
                    font-style: italic;
                    color: #666;
                }
                .article-summary ul, .article-summary ol {
                    margin: 10px 0;
                    padding-left: 25px;
                }
                .article-summary li {
                    margin: 5px 0;
                }
                .article-meta { 
                    font-size: 0.9em; 
                    color: #777; 
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px solid #eee;
                }
                .article-meta a {
                    color: #3498db;
                    text-decoration: none;
                }
                .article-meta a:hover {
                    text-decoration: underline;
                }
                .topic-tag { 
                    background: #3498db; 
                    color: white; 
                    padding: 3px 10px; 
                    border-radius: 3px; 
                    margin-right: 10px;
                    display: inline-block;
                    font-size: 0.85em;
                    font-weight: 500;
                }
                .header { 
                    background: #2c3e50; 
                    color: white; 
                    padding: 25px; 
                    border-radius: 5px; 
                    margin-bottom: 25px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0 0 10px 0;
                    font-size: 2em;
                }
                .header p {
                    margin: 0;
                    font-size: 1.1em;
                    opacity: 0.9;
                }
                .footer { 
                    margin-top: 30px; 
                    padding: 20px; 
                    background: #ecf0f1; 
                    border-radius: 5px; 
                    text-align: center; 
                    color: #7f8c8d; 
                    font-size: 0.9em;
                }
                .footer p {
                    margin: 5px 0;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Latest News Articles</h1>
                <p>""" + datetime.now().strftime('%B %d, %Y') + """</p>
            </div>
        """
        
        image_counter = 0
        for i, article in enumerate(articles, 1):
            html_body += f'<div class="article">'
            html_body += f'<div class="article-title">{i}. {article.title}</div>'
            
            # Add image if available
            if article.image_path and os.path.exists(article.image_path):
                image_cid = f"image{image_counter}"
                html_body += f'<img src="cid:{image_cid}" class="article-image" alt="{article.title}"/>'
                image_counter += 1
            
            html_body += f'<div class="article-summary">{markdown_to_html(article.summary)}</div>'
            html_body += f'<div class="article-meta">'
            html_body += f'<span class="topic-tag">{article.topic}</span>'
            html_body += f'<a href="{article.url}" target="_blank">Read Full Article</a>'
            html_body += f'</div>'
            html_body += f'</div>'
        
        html_body += """
            <div class="footer">
                <p><strong>MRA News Agent</strong></p>
                <p>Automated news delivery powered by local AI</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach images inline (referenced by CID in HTML)
        image_counter = 0
        for article in articles:
            if article.image_path and os.path.exists(article.image_path):
                try:
                    with open(article.image_path, 'rb') as img_file:
                        img_data = img_file.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-ID', f'<image{image_counter}>')
                        image.add_header('Content-Disposition', 'inline', filename=os.path.basename(article.image_path))
                        msg.attach(image)
                        image_counter += 1
                        logger.info(f"Attached image: {article.image_path}")
                except Exception as e:
                    logger.warning(f"Failed to attach image {article.image_path}: {e}")
        
        # Send email
        server = smtplib.SMTP(EMAIL_SMTP_HOST, int(EMAIL_SMTP_PORT))
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Successfully sent email with {len(articles)} articles")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False