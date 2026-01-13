"""
Image Generation Module
This module provides image generation functionality for news articles using TwistedPic.
"""

import os
import requests
import logging
import base64
from typing import Optional
from pathlib import Path
from models import NewsArticle
from config import (
    ENABLE_IMAGE_GENERATION,
    TWISTEDPIC_URL,
    IMAGE_MODEL,
    IMAGE_RESOLUTION,
    IMAGE_STEPS,
    IMAGE_CFG
)

def generate_article_image(article: NewsArticle) -> NewsArticle:
    """
    Generate an image for the article using TwistedPic
    """
    logger = logging.getLogger(__name__)
    
    if not ENABLE_IMAGE_GENERATION:
        logger.debug("Image generation disabled in config")
        return article
    
    logger.info(f"Starting image generation for article: '{article.title}'")
    
    try:
        # Create a prompt based on article title and summary
        prompt = f"Photo realistic image of {article.summary[:200]}"
        logger.info(f"Generated prompt: {prompt[:100]}...")
        
        # Send request to TwistedPic with correct API parameters
        logger.info(f"Sending request to TwistedPic at {TWISTEDPIC_URL}")
        response = requests.post(
            f"{TWISTEDPIC_URL}/api/generate",
            json={
                "user_prompt": prompt,
                "use_distortion": False,  # No distortion for news images
                "use_refinement": True,
                "distortion_mode": "echo_er",
                "distortion_tone": "neutral",
                "distortion_gain": 5,
                "image_model": IMAGE_MODEL,  # sd3_large or sdxl_base
                "num_inference_steps": IMAGE_STEPS,  # Optimized for SD3
                "guidance_scale": IMAGE_CFG,      # Optimized for SD3
                "resolution_preset": IMAGE_RESOLUTION,  # landscape, portrait, or square
                "use_random_seed": True
            },
            timeout=180  # Increased timeout for SD3 generation (~30-60s)
        )
        
        if response.status_code == 200:
            # Save the generated image
            image_data = response.json().get("image_base64", "")
            if image_data:
                # Create image file path
                timestamp = article.timestamp.replace(":", "-").replace(".", "-")
                image_filename = f"news_{timestamp}_{article.topic.replace(' ', '_')[:20]}.png"
                image_path = Path("data") / "images" / image_filename
                image_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Decode and save image
                image_bytes = base64.b64decode(image_data)
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                article.image_path = str(image_path)
                logger.info(f"✓ Image saved successfully: {image_path}")
            else:
                logger.warning(f"No image data in response for '{article.title}'")
                
        else:
            logger.warning(f"Image generation failed for article '{article.title}': {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to TwistedPic server at {TWISTEDPIC_URL}: {e}")
        logger.error("Make sure TwistedPic server is running (python server.py in TwistedPic folder)")
    except requests.exceptions.Timeout as e:
        logger.error(f"TwistedPic request timed out for article '{article.title}': {e}")
    except Exception as e:
        logger.error(f"Error generating image for article '{article.title}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Continue without image if generation fails
        
    return article