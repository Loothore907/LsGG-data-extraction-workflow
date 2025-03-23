# core/utils.py
"""
Shared utility functions used across all modules.
"""

from datetime import datetime
import re
import json

def generate_unique_name(url: str) -> str:
    """
    Generate a unique name based on URL and timestamp.
    
    Args:
        url (str): The source URL
        
    Returns:
        str: A unique identifier
    """
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S_%f')
    domain = re.sub(r'\W+', '_', url.split('//')[-1].split('/')[0])
    return f"{domain}_{timestamp}"

def extract_product_metadata(product_name: str) -> dict:
    """
    Extract metadata from a product name string.
    Attempts to identify weight, unit, and product type.
    
    Args:
        product_name (str): Product name
        
    Returns:
        dict: Extracted metadata
    """
    metadata = {
        "weight": None,
        "unit": None,
        "category": None
    }
    
    # Extract weight and unit (e.g., ".5g", "1g", "3.5g", "100mg")
    weight_pattern = r'(\d+(?:\.\d+)?)\s*(g|mg|oz)'
    weight_match = re.search(weight_pattern, product_name)
    if weight_match:
        metadata["weight"] = weight_match.group(1)
        metadata["unit"] = weight_match.group(2)
    
    # Extract category based on common keywords
    if any(kw in product_name.lower() for kw in ["flower", "deli"]):
        metadata["category"] = "flower"
    elif any(kw in product_name.lower() for kw in ["preroll", "pre-roll", "pre roll"]):
        metadata["category"] = "preroll"
    elif any(kw in product_name.lower() for kw in ["cartridge", "cart", "vape"]):
        metadata["category"] = "cartridge"
    elif any(kw in product_name.lower() for kw in ["edible", "gummies", "cookies"]):
        metadata["category"] = "edible"
    elif any(kw in product_name.lower() for kw in ["concentrate", "sugar", "sauce", "wax", "hash"]):
        metadata["category"] = "concentrate"
    
    return metadata

def clean_price(price_str: str) -> float:
    """
    Convert price string to float.
    
    Args:
        price_str (str): Price string (e.g., "$21.00")
        
    Returns:
        float: Cleaned price value
    """
    if not price_str:
        return None
    
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[^\d.]', '', price_str)
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def load_json_file(filepath: str) -> dict:
    """
    Load and parse JSON file.
    
    Args:
        filepath (str): Path to JSON file
        
    Returns:
        dict: Parsed JSON data
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None