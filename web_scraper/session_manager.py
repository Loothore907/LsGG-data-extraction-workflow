import os
import json
from .file_storage import FileStorage

class SessionManager:
    def __init__(self, storage=None):
        self.storage = storage or FileStorage()
        
    def create_session(self, vendor, initial_config):
        """Create a new scraping session"""
        session_id, session_path = self.storage.create_session_dir(vendor)
        
        # Save the initial configuration
        self.storage.save_mapping(session_path, initial_config)
        
        return {
            "session_id": session_id,
            "session_path": session_path,
            "vendor": vendor,
            "config": initial_config
        }
    
    def get_session(self, session_id):
        """Load an existing session"""
        if not session_id.startswith("session_"):
            session_id = f"session_{session_id}"
            
        session_path = os.path.join(self.storage.base_dir, session_id)
        
        if not os.path.exists(session_path):
            return None
            
        config_path = os.path.join(session_path, "scrape_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
            
        # Extract vendor from session_id
        parts = session_id.split('_')
        vendor = parts[1] if len(parts) > 1 else "unknown"
        
        return {
            "session_id": session_id,
            "session_path": session_path,
            "vendor": vendor,
            "config": config
        }
        
    def update_session_config(self, session_id, new_config):
        """Update configuration for an existing session"""
        session = self.get_session(session_id)
        if not session:
            return False
            
        # Merge new config with existing
        config = session["config"]
        config.update(new_config)
        
        # Save updated config
        self.storage.save_mapping(session["session_path"], config)
        return True 