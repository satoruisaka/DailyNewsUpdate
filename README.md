# News Agent for MRA

This module provides an automated news delivery system that fetches, processes, and delivers news articles to MRA. It includes functionality for:

1. Scheduled news fetching based on configurable topics
2. Translation of articles to English if needed
3. Summarization of content to less than 200 words
4. Image generation using TwistedPic
5. Email delivery of articles
6. Integration with MRA's data directory structure

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   News Topics   │    │  News Fetcher    │    │  Content Processor │
│   (config)      │───▶│  (Web Search)    │───▶│  (Translate,      │
│                 │    │                  │    │   Summarize)      │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                            │                        │
                            ▼                        ▼
                  ┌──────────────────┐    ┌──────────────────┐
                  │  Image Generator │    │  Email Delivery  │
                  │  (TwistedPic)    │    │  (SMTP)          │
                  └──────────────────┘    └──────────────────┘
                            │                        │
                            ▼                        ▼
                  ┌──────────────────┐    ┌──────────────────┐
                  │  MRA Integration │    │  MRA Data        │
                  │  (Save Articles) │    │  Storage         │
                  └──────────────────┘    └──────────────────┘
```

## Features

- Configurable news topics via `config.py`
- Automatic translation using LLMs
- Summarization to under 200 words
- Image generation with TwistedPic
- Email delivery via SMTP
- Integration with MRA's existing data structure
- Scheduled execution capability

## Installation

1. Create a virtual environment:
   ```bash
   cd NewsAgent
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama and required models:
   - Install Ollama from https://ollama.com/
   - Pull required models:
     ```bash
     ollama pull ministral-3:14b
     ```

4. Install TwistedPic for image generation:
   - Follow TwistedPic installation instructions

## Configuration

Configuration is handled through `config.py`:
- Set news topics in `NEWS_TOPICS`
- Configure email settings via environment variables:
  ```bash
  export EMAIL_USERNAME="your_email@gmail.com"
  export EMAIL_PASSWORD="your_app_password"
  export EMAIL_RECIPIENT="recipient@example.com"
  ```

## Usage

### Manual Execution
```bash
python main.py
```

### Automated Execution
Set up a cron job:
```bash
# Run daily at 9 AM
0 9 * * * /path/to/newsagent/main.py schedule
```

## Components

1. **config.py** - Configuration settings
2. **news_fetcher.py** - Core news fetching and processing (using Brave Web Search API)
3. **translation.py** - Translation functionality
4. **summarization.py** - Summarization functionality
5. **image_generation.py** - Image generation using TwistedPic
6. **email_delivery.py** - Email notification system
7. **integration.py** - MRA data integration
8. **scheduler.py** - Scheduled execution system
9. **main.py** - Main entry point

## Integration with MRA

The NewsAgent integrates seamlessly with existing MRA components:
- Articles are stored in `MRA/data/markdown/news_articles/`
- Automatically indexed by MRA's FAISS system
- Searchable through MRA's existing search interface
- Can be referenced in MRA sessions