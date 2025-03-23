#!/usr/bin/env python
"""
Entry point script to run the web scraper application.
This ensures the proper Python path is set up for imports.
"""
import sys
import os

# Add project root to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Run the streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    # Get the path to the web_scraper/app.py file
    app_path = os.path.join(root_dir, "web_scraper", "app.py")
    
    # Run the streamlit CLI with our app
    sys.argv = ["streamlit", "run", app_path, "--server.address=0.0.0.0"]
    sys.exit(stcli.main()) 