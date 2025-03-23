# markdown.py

import asyncio
import random
import time
from typing import List
from core.utils import generate_unique_name
from crawl4ai import AsyncWebCrawler
from .asyncio_helper import ensure_event_loop
from .file_storage import FileStorage

# List of common user agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

async def get_fit_markdown_async(url: str) -> str:
    """
    Async function using crawl4ai's AsyncWebCrawler to produce the regular raw markdown.
    Enhanced with anti-scraping measures:
    - Rotating user agents
    - Random delays
    - Proper headers
    """
    # Ensure event loop exists in this thread
    ensure_event_loop()
    
    # Add random delay to avoid rate limiting (0.5 to 3 seconds)
    await asyncio.sleep(random.uniform(0.5, 3))
    
    # Select a random user agent
    user_agent = random.choice(USER_AGENTS)
    
    # Setup enhanced headers
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }
    
    # Special case for weedmaps.com
    if "weedmaps.com" in url:
        print(f"Detected weedmaps.com - using enhanced scraping techniques")
        # Additional headers for weedmaps
        headers.update({
            "Referer": "https://www.google.com/",
            "DNT": "1",  # Do Not Track
        })
        # Extra delay for weedmaps
        await asyncio.sleep(random.uniform(1, 2))
    
    # Configure crawler with enhanced options
    crawler_config = {
        "headers": headers,
        "timeout": 30,
        "wait_for": 2000,  # Wait 2 seconds for JS to load
        "playwright_args": {
            "headless": True,
        }
    }

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, **crawler_config)
            if result.success:
                return result.markdown
            else:
                print(f"Failed to fetch markdown for {url}: {result.error if hasattr(result, 'error') else 'Unknown error'}")
                return ""
    except Exception as e:
        print(f"Exception while fetching markdown for {url}: {str(e)}")
        return ""


def fetch_fit_markdown(url: str) -> str:
    """
    Synchronous wrapper around get_fit_markdown_async().
    """
    # Use ensure_event_loop instead of creating a new one
    loop = ensure_event_loop()
    try:
        return loop.run_until_complete(get_fit_markdown_async(url))
    finally:
        # Don't close the loop, as it might be used elsewhere
        pass


def read_raw_data(file_path: str) -> str:
    """Read raw data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading raw data: {e}")
        return ""


def fetch_and_store_markdowns(session_path: str, urls: List[str]) -> List[str]:
    """Fetch and store markdown to files instead of database"""
    file_paths = []
    file_storage = FileStorage()

    for url in urls:
        # Check if we already have raw_data in files
        # This would need a way to locate existing files - perhaps by session and URL
        # For now, always fetch new data
        fit_md = fetch_fit_markdown(url)
        file_path = file_storage.save_raw_data(session_path, url, fit_md)
        file_paths.append(file_path)

    return file_paths
