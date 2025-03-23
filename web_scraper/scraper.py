# scraper.py

import json
from typing import List, Dict, Any
from pydantic import BaseModel, create_model, Field
from .assets import (OPENAI_MODEL_FULLNAME,GEMINI_MODEL_FULLNAME,SYSTEM_MESSAGE)
from .llm_calls import (call_llm_model)
from .markdown import read_raw_data
from core.utils import generate_unique_name
from .file_storage import FileStorage
import re
from bs4 import BeautifulSoup

def create_dynamic_listing_model(fields: List[str]):
    """Create a Pydantic model with the fields provided by the user"""
    field_dict = {field: (str, Field(description=f"{field} of the listing")) for field in fields}
    return create_model("DynamicListingModel", **field_dict)

def create_listings_container_model(listing_model):
    """Create a container model that wraps a list of listing models"""
    return create_model(
        "DynamicListingsContainer",
        listings=(List[listing_model], Field(description="List of listings extracted from the page"))
    )

def generate_system_message(listing_model: BaseModel) -> str:
    # same logic as your code
    schema_info = listing_model.model_json_schema()
    field_descriptions = []
    for field_name, field_info in schema_info["properties"].items():
        field_type = field_info["type"]
        field_descriptions.append(f'"{field_name}": "{field_type}"')

    schema_structure = ",\n".join(field_descriptions)

    final_prompt= SYSTEM_MESSAGE+"\n"+f"""strictly follows this schema:
    {{
       "listings": [
         {{
           {schema_structure}
         }}
       ]
    }}
    """

    return final_prompt

def save_formatted_data(session_path: str, url: str, data):
    """Save formatted data to file"""
    file_storage = FileStorage()
    
    # Convert Pydantic model to dict if needed
    if hasattr(data, "dict"):
        data_dict = data.dict()
    elif hasattr(data, "model_dump"):
        data_dict = data.model_dump()
    else:
        data_dict = data
    
    return file_storage.save_formatted_data(session_path, url, data_dict)

def extract_weedmaps_data(raw_data: str, fields: List[str], container_model) -> Dict:
    """
    Specialized extractor for weedmaps.com data
    Falls back to LLM if this doesn't find anything
    """
    # Create an empty container that matches the expected format
    empty_container = {
        "listings": []
    }
    
    # Try to parse the markdown with BeautifulSoup
    # Since markdown is basically HTML, we can use it directly
    soup = BeautifulSoup(raw_data, 'html.parser')
    
    # Look for product cards
    product_cards = soup.find_all('div', class_=lambda c: c and ('product-card' in c or 'ProductCard' in c))
    
    if not product_cards:
        # Try a different selector if product cards aren't found
        product_cards = soup.find_all('a', href=lambda h: h and '/product/' in h)
    
    if not product_cards:
        # One more attempt with a broader selector
        product_cards = soup.find_all(['div', 'a'], attrs={'data-testid': lambda t: t and ('product' in t.lower() if t else False)})
    
    # If we found product cards, extract data
    if product_cards:
        print(f"Found {len(product_cards)} product cards")
        
        for card in product_cards:
            listing = {}
            
            # Try to extract each requested field
            for field in fields:
                field_value = ""
                field_lower = field.lower()
                
                # Product name
                if field_lower in ['product_name', 'product', 'name', 'title']:
                    # Try several selectors that might contain the product name
                    name_elem = card.find(['h2', 'h3', 'h4', 'div'], class_=lambda c: c and ('name' in c.lower() or 'title' in c.lower() if c else False))
                    if name_elem:
                        field_value = name_elem.get_text(strip=True)
                
                # Price
                elif field_lower in ['price', 'cost', 'amount']:
                    price_elem = card.find(['span', 'div'], class_=lambda c: c and ('price' in c.lower() or 'cost' in c.lower() if c else False))
                    if price_elem:
                        field_value = price_elem.get_text(strip=True)
                
                # Brand
                elif field_lower in ['brand', 'vendor', 'manufacturer']:
                    brand_elem = card.find(['span', 'div'], class_=lambda c: c and ('brand' in c.lower() or 'vendor' in c.lower() if c else False))
                    if brand_elem:
                        field_value = brand_elem.get_text(strip=True)
                
                # General case - look for elements with class or ID containing the field name
                if not field_value:
                    elem = card.find(['div', 'span', 'p'], class_=lambda c: c and (field_lower in c.lower() if c else False))
                    if elem:
                        field_value = elem.get_text(strip=True)
                
                listing[field] = field_value
            
            # Only add listings that have at least one non-empty field
            if any(listing.values()):
                empty_container["listings"].append(listing)
    
    # Return parsed data
    return empty_container

def scrape_urls(session_path: str, file_paths: List[str], urls: List[str], fields: List[str], selected_model: str):
    """
    For each file_path:
      1) read raw_data from file
      2) parse with selected LLM
      3) save formatted_data
      4) accumulate cost
    Return total usage + list of final parsed data
    """
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0
    parsed_results = []

    DynamicListingModel = create_dynamic_listing_model(fields)
    DynamicListingsContainer = create_listings_container_model(DynamicListingModel)

    for i, file_path in enumerate(file_paths):
        raw_data = read_raw_data(file_path)
        if not raw_data:
            BLUE = "\033[34m"
            RESET = "\033[0m"
            print(f"{BLUE}No raw_data found for {file_path}, skipping.{RESET}")
            continue

        url = urls[i] if i < len(urls) else "unknown_url"
        
        # Check if this is a weedmaps URL and use specialized extraction first
        if "weedmaps.com" in url:
            print(f"Detected weedmaps.com URL - using specialized extraction")
            
            # Try weedmaps-specific extraction first
            weedmaps_data = extract_weedmaps_data(raw_data, fields, DynamicListingsContainer)
            
            # If we found data, use it; otherwise fall back to LLM
            if weedmaps_data and weedmaps_data.get("listings") and len(weedmaps_data["listings"]) > 0:
                print(f"Successfully extracted {len(weedmaps_data['listings'])} products with specialized extractor")
                parsed = weedmaps_data
                token_counts = {"input_tokens": 0, "output_tokens": 0}
                cost = 0
            else:
                # Fall back to LLM
                print(f"Specialized extraction found no data, falling back to LLM")
                parsed, token_counts, cost = call_llm_model(raw_data, DynamicListingsContainer, selected_model, SYSTEM_MESSAGE)
        else:
            # Standard LLM-based extraction for other sites
            parsed, token_counts, cost = call_llm_model(raw_data, DynamicListingsContainer, selected_model, SYSTEM_MESSAGE)

        # store
        output_path = save_formatted_data(session_path, url, parsed)

        total_input_tokens += token_counts["input_tokens"]
        total_output_tokens += token_counts["output_tokens"]
        total_cost += cost
        parsed_results.append({"file_path": file_path, "output_path": output_path, "parsed_data": parsed})

    return total_input_tokens, total_output_tokens, total_cost, parsed_results
