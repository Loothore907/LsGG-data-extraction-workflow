import os
import json
from datetime import datetime

class FileStorage:
    def __init__(self, base_dir="/app/output/web_crawler"):
        self.base_dir = base_dir
        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)
        print(f"FileStorage initialized with base directory: {os.path.abspath(self.base_dir)}")
        
    def create_session_dir(self, vendor):
        """Create a new session directory with timestamp and vendor name"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        session_id = f"session_{vendor}_{timestamp}"
        session_path = os.path.join(self.base_dir, session_id)
        os.makedirs(session_path, exist_ok=True)
        print(f"Created session directory: {os.path.abspath(session_path)}")
        return session_id, session_path
        
    def save_raw_data(self, session_path, url, raw_data):
        """Save raw markdown data to file"""
        vendor = self._extract_brand_from_url(url)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{vendor}_raw_data.md"
        file_path = os.path.join(session_path, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(raw_data)
            print(f"Successfully saved raw data to: {os.path.abspath(file_path)}")
            return file_path
        except Exception as e:
            print(f"Error saving raw data: {e}")
            return None
    
    def save_formatted_data(self, session_path, url, formatted_data):
        """Save formatted JSON data to file"""
        vendor = self._extract_brand_from_url(url)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{vendor}_formatted_data.json"
        file_path = os.path.join(session_path, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, indent=2)
            print(f"Successfully saved formatted data to: {os.path.abspath(file_path)}")
            return file_path
        except Exception as e:
            print(f"Error saving formatted data: {e}")
            return None
    
    def save_pagination_data(self, session_path, url, pagination_data):
        """Save pagination data to file"""
        vendor = self._extract_brand_from_url(url)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{vendor}_pagination.json"
        file_path = os.path.join(session_path, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(pagination_data, f, indent=2)
            print(f"Successfully saved pagination data to: {os.path.abspath(file_path)}")
            return file_path
        except Exception as e:
            print(f"Error saving pagination data: {e}")
            return None
    
    def read_raw_data(self, file_path):
        """Read raw data from file"""
        if not os.path.exists(file_path):
            return ""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_brand_from_url(self, url):
        """Extract brand name from URL"""
        # Looking at your sample URL: https://weedmaps.com/brands/enlighten/products/
        # We'll extract 'enlighten'
        parts = url.split('/')
        brands_index = -1
        for i, part in enumerate(parts):
            if part == 'brands':
                brands_index = i
                break
        
        if brands_index >= 0 and brands_index + 1 < len(parts):
            return parts[brands_index + 1]
        return "unknown"
        
    def save_mapping(self, session_path, config):
        """Save configuration mapping for future reuse"""
        filename = "scrape_config.json"
        file_path = os.path.join(session_path, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"Successfully saved mapping data to: {os.path.abspath(file_path)}")
            return file_path
        except Exception as e:
            print(f"Error saving mapping data: {e}")
            return None
    
    def list_sessions(self):
        """List all available sessions"""
        if not os.path.exists(self.base_dir):
            return []
            
        sessions = []
        for item in os.listdir(self.base_dir):
            if os.path.isdir(os.path.join(self.base_dir, item)) and item.startswith("session_"):
                sessions.append(item)
        return sessions 

    def list_session_files(self, session_path):
        """List all files in a session directory"""
        if not os.path.exists(session_path):
            print(f"Session path does not exist: {session_path}")
            return []
        
        files = []
        try:
            for file in os.listdir(session_path):
                file_path = os.path.join(session_path, file)
                if os.path.isfile(file_path):
                    files.append(file)
            print(f"Found {len(files)} files in session directory: {session_path}")
            for file in files:
                print(f"  - {file}")
            return files
        except Exception as e:
            print(f"Error listing session files: {e}")
            return [] 