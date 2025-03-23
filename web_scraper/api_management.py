import streamlit as st
import os
from dotenv import load_dotenv
from .assets import MODELS_USED

load_dotenv()
def get_api_key(model):
    """
    Returns an API key for a given model by:
      1) Looking up the environment var name in MODELS_USED[model].
         (We assume there's exactly one item in that set.)
      2) Returning the key from st.session_state if present;
         otherwise from os.environ.
    """
    env_var_name = list(MODELS_USED[model])[0]  # e.g., "GEMINI_API_KEY"
    return st.session_state.get(env_var_name) or os.getenv(env_var_name)

# The following functions are no longer needed since we migrated to file-based storage
# They're replaced with empty implementations to prevent import errors
def get_supabase_client():
    """
    This function is deprecated. We now use file-based storage instead of Supabase.
    Returns None to indicate Supabase is not available.
    """
    return None

def get_supabase_admin_client():
    """
    This function is deprecated. We now use file-based storage instead of Supabase.
    Returns None to indicate Supabase is not available.
    """
    return None
