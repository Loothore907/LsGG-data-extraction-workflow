# core/config.py
"""
Configuration management for all modules.
Handles environment variables, settings, and configuration across the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Centralized configuration management.
    Provides access to environment variables and settings.
    """
    
    # File paths
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    
    # Supabase configuration (legacy)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # AI Model API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    @classmethod
    def get_api_key(cls, key_name):
        """
        Get API key by name
        """
        return getattr(cls, key_name, None)
    
    @classmethod
    def ensure_output_dir(cls, module_name):
        """
        Ensure the output directory exists for a specific module
        Returns the path to the module's output directory
        """
        module_dir = os.path.join(cls.OUTPUT_DIR, module_name)
        os.makedirs(module_dir, exist_ok=True)
        return module_dir