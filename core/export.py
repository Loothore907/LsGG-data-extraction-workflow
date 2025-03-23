# core/export.py
"""
File export functionality for all modules.
Handles consistent data format and file naming for output files.
"""

import json
import os
from datetime import datetime
import uuid

def generate_filename(vendor_id=None, source_type="generic"):
    """
    Generate a standardized filename for data export.
    
    Args:
        vendor_id (str, optional): Vendor identifier, if applicable
        source_type (str): Source module type (web_scraper, voice_processor, etc.)
    
    Returns:
        str: Standardized filename
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if vendor_id:
        return f"{vendor_id}_{timestamp}_{source_type}.json"
    else:
        # Generate a random ID if no vendor ID is provided
        random_id = str(uuid.uuid4())[:8]
        return f"unknown_vendor_{random_id}_{timestamp}_{source_type}.json"

def export_data(data, module_name, vendor_id=None, region=None, source_url=None):
    """
    Export data to a JSON file in the standardized format.
    
    Args:
        data (list): List of products or other data items
        module_name (str): Name of the module (web_scraper, voice_processor, etc.)
        vendor_id (str, optional): Vendor identifier, if applicable
        region (str, optional): Geographic region identifier
        source_url (str, optional): Source URL or identifier
    
    Returns:
        tuple: (bool success, str filepath)
    """
    from core.config import Config
    
    # Ensure output directory exists
    output_dir = Config.ensure_output_dir(module_name)
    
    # Generate filename
    filename = generate_filename(vendor_id, module_name)
    filepath = os.path.join(output_dir, filename)
    
    # Create structured output
    output = {
        "metadata": {
            "source": module_name,
            "timestamp": datetime.now().isoformat(),
            "vendor_id": vendor_id or "unknown",
            "region": region or "unknown",
            "source_url": source_url
        },
        "products": data
    }
    
    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return True, filepath
    except Exception as e:
        print(f"Error exporting data: {e}")
        return False, None