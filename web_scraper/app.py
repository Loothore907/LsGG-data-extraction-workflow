# app.py
# Add these lines at the very top of app.py
import asyncio
import nest_asyncio
import sys
import os
from datetime import datetime

# Add the path adjustment to allow imports from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the current file's directory to path to ensure we can import from the web_scraper package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Fix for the asyncio event loop error in Streamlit
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
nest_asyncio.apply()

# Continue with your existing imports and code
# Now import streamlit and other modules
import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
import re
import threading

# Use absolute imports to avoid relative import errors in Docker
# Check if running as script or imported as module
if __name__ == "__main__" or os.environ.get("DOCKER_ENVIRONMENT", "false") == "true":
    # When running directly or in Docker, use absolute imports
    from web_scraper.asyncio_helper import ensure_event_loop
    from web_scraper.scraper import scrape_urls
    from web_scraper.pagination import paginate_urls
    from web_scraper.markdown import fetch_and_store_markdowns
    from web_scraper.assets import MODELS_USED
    from web_scraper.file_storage import FileStorage
    from web_scraper.session_manager import SessionManager
else:
    # When imported as part of a package, use relative imports
    from .asyncio_helper import ensure_event_loop
    from .scraper import scrape_urls
    from .pagination import paginate_urls
    from .markdown import fetch_and_store_markdowns
    from .assets import MODELS_USED
    from .file_storage import FileStorage
    from .session_manager import SessionManager

# Apply the helper function to ensure we have an event loop
ensure_event_loop()

# Initialize Streamlit app
st.set_page_config(page_title="Universal Web Scraper", page_icon="🦑")

st.title("Universal Web Scraper 🦑")

# Initialize session state variables
if 'scraping_state' not in st.session_state:
    st.session_state['scraping_state'] = 'idle'  # Possible states: 'idle', 'waiting', 'scraping', 'completed'
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'driver' not in st.session_state:
    st.session_state['driver'] = None
# Add session management features
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = None
if 'session_path' not in st.session_state:
    st.session_state['session_path'] = None

# Sidebar components
st.sidebar.title("Web Scraper Settings")

# API Keys
with st.sidebar.expander("API Keys", expanded=False):
    # Loop over every model in MODELS_USED
    for model, required_keys in MODELS_USED.items():
        # required_keys is a set (e.g. {"GEMINI_API_KEY"})
        for key_name in required_keys:
            # Create a password-type text input for each API key
            # st.session_state[key_name] = 
            st.text_input(key_name,type="password",key=key_name)

# Model selection
model_selection = st.sidebar.selectbox("Select Model", options=list(MODELS_USED.keys()), index=0)
st.sidebar.markdown("---")
st.sidebar.write("## URL Input Section")
# Ensure the session state for our URL list exists
if "urls_splitted" not in st.session_state:
    st.session_state["urls_splitted"] = []

with st.sidebar.container():
    col1, col2 = st.columns([3, 1], gap="small")
    
    with col1:
        # A text area to paste multiple URLs at once
        if "text_temp" not in st.session_state:
            st.session_state["text_temp"] = ""

        url_text = st.text_area("Enter one or more URLs (space/tab/newline separated):",st.session_state["text_temp"], key="url_text_input", height=68)

    with col2:
        if st.button("Add URLs"):
            if url_text.strip():
                new_urls = re.split(r"\s+", url_text.strip())
                new_urls = [u for u in new_urls if u]
                st.session_state["urls_splitted"].extend(new_urls)
                st.session_state["text_temp"] = ""
                st.rerun()
        if st.button("Clear URLs"):
            st.session_state["urls_splitted"] = []
            st.rerun()

    # Show the URLs in an expander, each as a styled "bubble"
    with st.expander("Added URLs", expanded=True):
        if st.session_state["urls_splitted"]:
            bubble_html = ""
            for url in st.session_state["urls_splitted"]:
                bubble_html += (
                    f"<span style='"
                    f"background-color: #E6F9F3;"  # Very Light Mint for contrast
                    f"color: #0074D9;"            # Bright Blue for link-like appearance
                    f"border-radius: 15px;"       # Slightly larger radius for smoother edges
                    f"padding: 8px 12px;"         # Increased padding for better spacing
                    f"margin: 5px;"               # Space between bubbles
                    f"display: inline-block;"     # Ensures proper alignment
                    f"text-decoration: none;"     # Removes underline if URLs are clickable
                    f"font-weight: bold;"         # Makes text stand out
                    f"font-family: Arial, sans-serif;"  # Clean and modern font
                    f"box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);'"  # Subtle shadow for depth
                    f">{url}</span>"
                )
            st.markdown(bubble_html, unsafe_allow_html=True)
        else:
            st.write("No URLs added yet.")

st.sidebar.markdown("---")


# Fields to extract
show_tags = st.sidebar.toggle("Enable Scraping")
fields = []
if show_tags:
    fields = st_tags_sidebar(label='Enter Fields to Extract:',text='Press enter to add a field',value=[],suggestions=[],maxtags=-1,key='fields_input')

st.sidebar.markdown("---")

# Pagination toggle and details
use_pagination = st.sidebar.toggle("Enable Pagination")
pagination_details = ""
if use_pagination:
    pagination_details = st.sidebar.text_input("Enter Pagination Details (optional)",help="Describe how to navigate through pages (e.g., 'Next' button class, URL pattern)")

st.sidebar.markdown("---")

# Display current session if active
if st.session_state.get('session_id'):
    st.sidebar.success(f"Active Session: {st.session_state['session_id']}")
    
    if st.sidebar.button("Clear Active Session"):
        st.session_state['session_id'] = None
        st.session_state['session_path'] = None
        st.rerun()

# Add Session Management
with st.sidebar.expander("Session Management"):
    # Option to create a new session
    vendor_name = st.text_input("Vendor Name (optional)", 
                              help="Auto-detected from URL if blank")
    
    if st.button("Start New Session"):
        # Extract vendor from URL if not specified
        if not vendor_name and st.session_state.get("urls_splitted"):
            url = st.session_state["urls_splitted"][0]
            vendor_name = FileStorage()._extract_brand_from_url(url)
        
        # Create initial config
        initial_config = {
            "urls": st.session_state.get("urls_splitted", []),
            "fields": fields,
            "model": model_selection,
            "use_pagination": use_pagination,
            "pagination_details": pagination_details
        }
        
        session_manager = SessionManager()
        session = session_manager.create_session(vendor_name, initial_config)
        
        st.session_state['session_id'] = session["session_id"]
        st.session_state['session_path'] = session["session_path"]
        st.success(f"Started new session: {session['session_id']}")
    
    # Option to load existing session
    session_manager = SessionManager()
    available_sessions = session_manager.storage.list_sessions()
    
    selected_session = st.selectbox("Load Existing Session", 
                                  ["None"] + available_sessions)
    
    if selected_session != "None" and st.button("Load Session"):
        session = session_manager.get_session(selected_session)
        if session:
            # Load configuration
            st.session_state["urls_splitted"] = session["config"].get("urls", [])
            st.session_state["model_selection"] = session["config"].get("model", model_selection)
            # Add more config loading as needed
            
            st.session_state['session_id'] = session["session_id"]
            st.session_state['session_path'] = session["session_path"]
            st.success(f"Loaded session: {session['session_id']}")

# Main action button
if st.sidebar.button("LAUNCH", type="primary"):
    if st.session_state["urls_splitted"] == []:
        st.error("Please enter at least one URL.")
    elif show_tags and len(fields) == 0:
        st.error("Please enter at least one field to extract.")
    else:
        # Save user choices
        st.session_state['urls'] = st.session_state["urls_splitted"]
        st.session_state['fields'] = fields
        st.session_state['model_selection'] = model_selection
        st.session_state['use_pagination'] = use_pagination
        st.session_state['pagination_details'] = pagination_details
        
        # Create a session if one doesn't exist
        if not st.session_state.get('session_id'):
            # Extract vendor from URL
            url = st.session_state["urls_splitted"][0]
            vendor_name = FileStorage()._extract_brand_from_url(url)
            
            # Create initial config
            initial_config = {
                "urls": st.session_state["urls_splitted"],
                "fields": fields,
                "model": model_selection,
                "use_pagination": use_pagination,
                "pagination_details": pagination_details
            }
            
            session_manager = SessionManager()
            session = session_manager.create_session(vendor_name, initial_config)
            
            st.session_state['session_id'] = session["session_id"]
            st.session_state['session_path'] = session["session_path"]
        
        # fetch or reuse the markdown for each URL
        file_paths = fetch_and_store_markdowns(st.session_state['session_path'], st.session_state["urls_splitted"])
        st.session_state["file_paths"] = file_paths

        # Move on to "scraping" step
        st.session_state['scraping_state'] = 'scraping'



if st.session_state['scraping_state'] == 'scraping':
    try:
        with st.spinner("Processing..."):
            file_paths = st.session_state["file_paths"]
            session_path = st.session_state['session_path']
            urls = st.session_state['urls']

            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0
            
            # 1) Scraping logic - modified to work with files
            all_data = []
            if show_tags:
                # Modified to use file paths and session path
                in_tokens_s, out_tokens_s, cost_s, parsed_data = scrape_urls(session_path, file_paths, urls, 
                                                                            st.session_state['fields'],
                                                                            st.session_state['model_selection'])
                total_input_tokens += in_tokens_s
                total_output_tokens += out_tokens_s
                total_cost += cost_s

                all_data = parsed_data
                st.session_state['in_tokens_s'] = in_tokens_s
                st.session_state['out_tokens_s'] = out_tokens_s
                st.session_state['cost_s'] = cost_s
                
            # 2) Pagination logic - similarly modified
            pagination_info = None
            if st.session_state['use_pagination']:
                in_tokens_p, out_tokens_p, cost_p, page_results = paginate_urls(session_path, file_paths, urls,
                                                                              st.session_state['model_selection'],
                                                                              st.session_state['pagination_details'])
                total_input_tokens += in_tokens_p
                total_output_tokens += out_tokens_p
                total_cost += cost_p

                pagination_info = page_results
                st.session_state['in_tokens_p'] = in_tokens_p
                st.session_state['out_tokens_p'] = out_tokens_p
                st.session_state['cost_p'] = cost_p
                
            # 3) Save everything in session state
            st.session_state['results'] = {
                'data': all_data,
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_cost': total_cost,
                'pagination_info': pagination_info
            }
            
            # 4) Update session mapping with results summary
            session_manager = SessionManager()
            results_summary = {
                'scrape_completed': True,
                'scrape_timestamp': datetime.now().isoformat(),
                'total_cost': total_cost,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens
            }
            session_manager.update_session_config(st.session_state['session_id'], results_summary)
            
            st.session_state['scraping_state'] = 'completed'
            
            # Display success message
            st.success(f"Scraping completed. Results saved to {session_path}")

            # Add debug info to verify files exist
            if st.session_state.get('session_path'):
                file_storage = FileStorage()
                session_files = file_storage.list_session_files(st.session_state['session_path'])
                if session_files:
                    with st.expander("View saved files"):
                        for file in session_files:
                            st.code(file)
    except Exception as e:
        st.error(f"An error occurred during scraping: {e}")
        st.session_state['scraping_state'] = 'idle'

# Display results
if st.session_state['scraping_state'] == 'completed' and st.session_state['results']:
    results = st.session_state['results']
    all_data = results['data']
    total_input_tokens = results['input_tokens']
    total_output_tokens = results['output_tokens']
    total_cost = results['total_cost']
    pagination_info = results['pagination_info']

    # Display scraping details
    # Debugging snippet inside your "Scraping Results" section

    if show_tags:
        st.subheader("Scraping Results")

        # We'll accumulate all rows in this list
        all_rows = []

        # Loop over each data item in the "all_data" list
        for i, data_item in enumerate(all_data, start=1):

            # Usually data_item is something like:
            # {"file_path": "...", "output_path": "...", "parsed_data": DynamicListingsContainer(...) or dict or str}

            # 1) Ensure data_item is a dict
            if not isinstance(data_item, dict):
                st.error(f"data_item is not a dict, skipping. Type: {type(data_item)}")
                continue

            # 2) If "parsed_data" is present and might be a Pydantic model or something
            if "parsed_data" in data_item:
                parsed_obj = data_item["parsed_data"]

                # Convert if it's a Pydantic model
                if hasattr(parsed_obj, "dict"):
                    parsed_obj = parsed_obj.model_dump()
                elif isinstance(parsed_obj, str):
                    # If it's a JSON string, attempt to parse
                    try:
                        parsed_obj = json.loads(parsed_obj)
                    except json.JSONDecodeError:
                        # fallback: just keep as raw string
                        pass

                # Now we have "parsed_obj" as a dict, list, or string
                data_item["parsed_data"] = parsed_obj

            # 3) If the "parsed_data" has a 'listings' key that is a list of items,
            #    we might want to treat them as multiple rows. 
            #    Otherwise, we treat the entire data_item as a single row.

            pd_obj = data_item["parsed_data"]

            # If it has 'listings' in parsed_data
            if isinstance(pd_obj, dict) and "listings" in pd_obj and isinstance(pd_obj["listings"], list):
                # We'll create one row per listing, plus carry over metadata fields
                for listing in pd_obj["listings"]:
                    # Make a shallow copy so we don't mutate 'listing'
                    row_dict = dict(listing)
                    # Add file_path and output_path metadata
                    row_dict["file_path"] = data_item.get("file_path", "")
                    row_dict["output_path"] = data_item.get("output_path", "")
                    all_rows.append(row_dict)
            else:
                # We'll just store the entire item as one row
                row_dict = dict(data_item)  # shallow copy
                all_rows.append(row_dict)

        # After collecting all rows from all_data in "all_rows", create one DataFrame
        if not all_rows:
            st.warning("No data rows to display.")
        else:
            df = pd.DataFrame(all_rows)
            st.dataframe(df, use_container_width=True)

        if "in_tokens_s" in st.session_state:
            st.sidebar.markdown("### Scraping Details")
            st.sidebar.markdown("#### Token Usage")
            st.sidebar.markdown(f"*Input Tokens:* {st.session_state['in_tokens_s']}")
            st.sidebar.markdown(f"*Output Tokens:* {st.session_state['out_tokens_s']}")
            st.sidebar.markdown(f"**Total Cost:** :green-background[**${st.session_state['cost_s']:.4f}**]")


        # Download options
        st.subheader("Download Extracted Data")
        col1, col2 = st.columns(2)
        with col1:
            json_data = json.dumps(all_data, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o), indent=4)
            st.download_button("Download JSON",data=json_data,file_name="scraped_data.json")
        with col2:
            # Convert all data to a single DataFrame
            all_listings = []
            for data in all_data:
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                
                # Extract parsed_data
                parsed_data = data.get('parsed_data', {})
                
                if isinstance(parsed_data, dict) and 'listings' in parsed_data:
                    all_listings.extend(parsed_data['listings'])
                elif hasattr(parsed_data, 'listings'):
                    all_listings.extend([item.dict() for item in parsed_data.listings])
                else:
                    all_listings.append(data)
            
            combined_df = pd.DataFrame(all_listings)
            st.download_button("Download CSV",data=combined_df.to_csv(index=False),file_name="scraped_data.csv")

        st.success(f"Scraping completed. Results saved to {st.session_state['session_path']}")

    # Display pagination info
    if pagination_info:
        all_page_rows = []

        # Iterate through pagination_info, which contains multiple items
        for i, item in enumerate(pagination_info, start=1):

            # Ensure item is a dictionary
            if not isinstance(item, dict):
                st.error(f"item is not a dict, skipping. Type: {type(item)}")
                continue

            # Check if "pagination_data" exists
            if "pagination_data" in item:
                pag_obj = item["pagination_data"]

                # Convert if it's a Pydantic model
                if hasattr(pag_obj, "dict"):
                    pag_obj = pag_obj.model_dump()
                elif isinstance(pag_obj, str):
                    # If it's a JSON string, attempt to parse
                    try:
                        pag_obj = json.loads(pag_obj)
                    except json.JSONDecodeError:
                        # Fallback: keep it as raw string
                        pass

                # Now we have pag_obj as a dict, list, or string
                item["pagination_data"] = pag_obj

            # Process the extracted pagination_data
            pd_obj = item["pagination_data"]

            # If it contains "page_urls" and it's a list, extract individual rows
            if isinstance(pd_obj, dict) and "page_urls" in pd_obj and isinstance(pd_obj["page_urls"], list):
                for page_url in pd_obj["page_urls"]:
                    row_dict = {
                        "page_url": page_url,
                        "file_path": item.get("file_path", ""),
                        "output_path": item.get("output_path", "")
                    }
                    all_page_rows.append(row_dict)
            else:
                # Otherwise, store the entire item as a single row
                row_dict = dict(item)  # Shallow copy
                all_page_rows.append(row_dict)

        # Create an empty DataFrame by default
        pagination_df = pd.DataFrame(columns=["page_url"])
        
        # Create DataFrame and display it
        if not all_page_rows:
            st.warning("No page URLs found.")
        else:
            pagination_df = pd.DataFrame(all_page_rows)
            
            # Configure columns for better display
            column_config = {
                "page_url": st.column_config.LinkColumn("Page URL"),
                "file_path": st.column_config.TextColumn("Source File"),
                "output_path": st.column_config.TextColumn("Output File")
            }
            
            st.markdown("---")
            st.subheader("Pagination Information")
            st.write("**Page URLs:**")
            st.dataframe(pagination_df, column_config=column_config, use_container_width=True)
        
        if "in_tokens_p" in st.session_state:
            # Display token usage and cost using metrics
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Pagination Details")
            st.sidebar.markdown(f"**Number of Page URLs:** {len(all_page_rows)}")
            st.sidebar.markdown("#### Pagination Token Usage")
            st.sidebar.markdown(f"*Input Tokens:* {st.session_state['in_tokens_p']}")
            st.sidebar.markdown(f"*Output Tokens:* {st.session_state['out_tokens_p']}")
            st.sidebar.markdown(f"**Total Cost:** :blue-background[**${st.session_state['cost_p']:.4f}**]")
        
        # Only show download buttons if we have pagination data
        if not all_page_rows:
            st.warning("No pagination URLs found to download.")
        else:
            # Download pagination URLs
            st.subheader("Download Pagination URLs")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("Download Pagination CSV",data=pagination_df.to_csv(index=False),file_name="pagination_urls.csv")
            with col2:
                st.download_button("Download Pagination JSON",data=json.dumps(all_page_rows, indent=4),file_name="pagination_urls.json")
        
        # Change the success message for pagination
        st.success(f"Pagination detection completed. Results saved to {st.session_state['session_path']}")

    # Reset scraping state
    if st.sidebar.button("Clear Results"):
        st.session_state['scraping_state'] = 'idle'
        st.session_state['results'] = None
        # Don't clear the session - just the results
        # st.session_state['session_id'] = None
        # st.session_state['session_path'] = None

    # If pagination has been performed, add a feature to scrape additional pages
    if ('results' in st.session_state and 
        st.session_state['results'] is not None and 
        'pagination_info' in st.session_state['results'] and 
        st.session_state['results']['pagination_info']):
        st.subheader("Continue Scraping Pagination")
        
        pagination_info = st.session_state['results']['pagination_info']
        all_page_urls = []
        
        # Extract all page URLs from pagination_info
        for item in pagination_info:
            if isinstance(item, dict) and "pagination_data" in item:
                pag_obj = item["pagination_data"]
                if isinstance(pag_obj, dict) and "page_urls" in pag_obj and isinstance(pag_obj["page_urls"], list):
                    all_page_urls.extend(pag_obj["page_urls"])
        
        # Display available page URLs
        if all_page_urls:
            st.write(f"Found {len(all_page_urls)} pagination URLs")
            
            # Calculate which pages have been scraped and which remain
            # (This would require tracking scraped URLs in the session config)
            
            # Allow selecting a range to scrape next
            col1, col2 = st.columns(2)
            with col1:
                start_idx = st.number_input("Start Page Index", min_value=0, max_value=len(all_page_urls)-1, value=0)
            with col2:
                end_idx = st.number_input("End Page Index", min_value=start_idx, max_value=len(all_page_urls)-1, 
                                        value=min(start_idx+3, len(all_page_urls)-1))
            
            # Display selected range
            selected_urls = all_page_urls[start_idx:end_idx+1]
            st.write("Selected URLs to scrape:")
            for i, url in enumerate(selected_urls):
                st.write(f"{i+1}. {url}")
            
            # Button to scrape selected pages
            if st.button("Scrape Selected Pages"):
                # Update URLs in session state
                st.session_state["urls_splitted"] = selected_urls
                
                # Disable pagination for this run (we're using pre-detected pages)
                st.session_state['use_pagination'] = False
                
                # Launch the scraper
                file_paths = fetch_and_store_markdowns(st.session_state['session_path'], selected_urls)
                st.session_state["file_paths"] = file_paths
                st.session_state['scraping_state'] = 'scraping'
                
                # Update session mapping
                session_manager = SessionManager()
                page_batch_info = {
                    f"page_batch_{datetime.now().strftime('%Y%m%d%H%M')}": {
                        "urls": selected_urls,
                        "start_idx": start_idx,
                        "end_idx": end_idx
                    }
                }
                session_manager.update_session_config(st.session_state['session_id'], page_batch_info)
                
                st.experimental_rerun()

    # If both scraping and pagination were performed, show totals under the pagination table
    if show_tags and pagination_info:
        st.markdown("---")
        st.markdown("### Total Counts and Cost (Including Pagination)")
        st.markdown(f"**Total Input Tokens:** {total_input_tokens}")
        st.markdown(f"**Total Output Tokens:** {total_output_tokens}")
        st.markdown(f"**Total Combined Cost:** :rainbow-background[**${total_cost:.4f}**]")

