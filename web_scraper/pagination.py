# pagination.py

import json
from typing import List, Dict
from .assets import PROMPT_PAGINATION
from .markdown import read_raw_data
from pydantic import BaseModel, Field
from typing import List
from pydantic import create_model
from .llm_calls import (call_llm_model)
from .file_storage import FileStorage
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse


class PaginationModel(BaseModel):
    page_urls: List[str]


def get_pagination_response_format():
    return PaginationModel


def create_dynamic_listing_model(field_names: List[str]):
    field_definitions = {field: (str, ...) for field in field_names}
    return create_model('DynamicListingModel', **field_definitions)

def build_pagination_prompt(indications: str, url: str) -> str:
    # Base prompt
    prompt = PROMPT_PAGINATION + f"\nThe page being analyzed is: {url}\n"

    if indications.strip():
        prompt += (
            "These are the user's indications. Pay attention:\n"
            f"{indications}\n\n"
        )
    else:
        prompt += (
            "No special user indications. Just apply the pagination logic.\n\n"
        )
    # Finally append the actual markdown data
    return prompt


def save_pagination_data(session_path: str, url: str, pagination_data) -> str:
    """Save pagination data to file instead of database"""
    file_storage = FileStorage()
    
    if hasattr(pagination_data, "dict"):
        pagination_data = pagination_data.dict()
    elif hasattr(pagination_data, "model_dump"):
        pagination_data = pagination_data.model_dump()
    elif isinstance(pagination_data, str):
        try:
            pagination_data = json.loads(pagination_data)
        except json.JSONDecodeError:
            pagination_data = {"raw_text": pagination_data}
    
    return file_storage.save_pagination_data(session_path, url, pagination_data)


def extract_weedmaps_pagination(raw_data: str, url: str) -> Dict:
    """
    Specialized function to extract pagination from weedmaps.com
    """
    # Create an empty result in the expected format
    empty_result = {
        "page_urls": []
    }
    
    # Parse the markdown/HTML with BeautifulSoup
    soup = BeautifulSoup(raw_data, 'html.parser')
    
    # Extract base URL for building absolute links
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Try different pagination selectors that might be present on weedmaps
    
    # First approach: Look for pagination container with page numbers
    pagination_container = soup.find('nav', class_=lambda c: c and ('pagination' in c.lower() if c else False))
    
    # Second approach: Look for ul/ol lists that might contain pagination
    if not pagination_container:
        pagination_container = soup.find(['ul', 'ol'], class_=lambda c: c and ('pagination' in c.lower() if c else False))
    
    # If we found a pagination container, extract links
    if pagination_container:
        page_links = pagination_container.find_all('a', href=True)
        
        for link in page_links:
            href = link.get('href')
            if href:
                # Build absolute URL if it's relative
                page_url = urljoin(base_url, href)
                if page_url not in empty_result["page_urls"]:
                    empty_result["page_urls"].append(page_url)
    
    # If no pagination container found, try a different approach with query parameters
    if not empty_result["page_urls"]:
        # Look for any links that might contain page=X or similar patterns
        all_links = soup.find_all('a', href=True)
        page_pattern = re.compile(r'[?&](page|p)=(\d+)', re.IGNORECASE)
        
        for link in all_links:
            href = link.get('href')
            if href and page_pattern.search(href):
                page_url = urljoin(base_url, href)
                if page_url not in empty_result["page_urls"]:
                    empty_result["page_urls"].append(page_url)
    
    # Finally, try to construct pagination URLs if we found page numbers but no proper links
    if not empty_result["page_urls"]:
        # Look for elements that might contain page numbers
        page_elements = soup.find_all(['span', 'a', 'div'], string=lambda s: s and s.isdigit() and len(s.strip()) < 5)
        
        # Extract numbers and sort them
        page_numbers = []
        for element in page_elements:
            try:
                num = int(element.get_text(strip=True))
                if 1 <= num <= 100:  # Reasonable page number range
                    page_numbers.append(num)
            except ValueError:
                continue
        
        # If we found page numbers, construct URLs
        if page_numbers:
            page_numbers = sorted(list(set(page_numbers)))
            
            # Determine URL pattern
            if '?' in url:
                page_param = '&page='
            else:
                page_param = '?page='
            
            for num in page_numbers:
                page_url = f"{url}{page_param}{num}"
                if page_url not in empty_result["page_urls"]:
                    empty_result["page_urls"].append(page_url)
    
    # Print debug info
    if empty_result["page_urls"]:
        print(f"Found {len(empty_result['page_urls'])} pagination URLs with specialized extractor")
    else:
        print("No pagination URLs found with specialized extractor")
    
    return empty_result


def paginate_urls(session_path: str, file_paths: List[str], urls: List[str], selected_model: str, indication: str):
    """
    For each file_path, read raw_data, detect pagination, save results,
    accumulate cost usage, and return a final summary.
    """
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0
    pagination_results = []

    for i, file_path in enumerate(file_paths):
        raw_data = read_raw_data(file_path)
        if not raw_data:
            BLUE = "\033[34m"
            RESET = "\033[0m"
            print(f"{BLUE}No raw_data found for {file_path}, skipping pagination.{RESET}")
            continue
            
        current_url = urls[i] if i < len(urls) else "unknown_url"
        
        # Check if this is a weedmaps URL and use specialized pagination detection
        if "weedmaps.com" in current_url:
            print(f"Detected weedmaps.com URL - using specialized pagination detection")
            
            # Try specialized pagination detection
            pag_data = extract_weedmaps_pagination(raw_data, current_url)
            
            # If we found pagination URLs, use them; otherwise fall back to LLM
            if pag_data and pag_data.get("page_urls") and len(pag_data["page_urls"]) > 0:
                print(f"Successfully extracted {len(pag_data['page_urls'])} pagination URLs with specialized extractor")
                token_counts = {"input_tokens": 0, "output_tokens": 0}
                cost = 0
            else:
                # Fall back to LLM
                print(f"Specialized pagination detection found no URLs, falling back to LLM")
                response_schema = get_pagination_response_format()
                full_indication = build_pagination_prompt(indication, current_url)
                pag_data, token_counts, cost = call_llm_model(raw_data, response_schema, selected_model, full_indication)
        else:
            # Standard LLM-based pagination detection for other sites
            response_schema = get_pagination_response_format()
            full_indication = build_pagination_prompt(indication, current_url)
            pag_data, token_counts, cost = call_llm_model(raw_data, response_schema, selected_model, full_indication)

        # store
        output_path = save_pagination_data(session_path, current_url, pag_data)

        # accumulate cost
        total_input_tokens += token_counts["input_tokens"]
        total_output_tokens += token_counts["output_tokens"]
        total_cost += cost

        pagination_results.append({"file_path": file_path, "output_path": output_path, "pagination_data": pag_data})

    return total_input_tokens, total_output_tokens, total_cost, pagination_results
