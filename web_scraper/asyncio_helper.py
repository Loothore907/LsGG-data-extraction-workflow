# asyncio_helper.py

import asyncio
import nest_asyncio
import sys
import threading

# Thread-local storage to track loop creation in each thread
_thread_local = threading.local()

def ensure_event_loop():
    """
    Ensures that the current thread has an event loop.
    If one doesn't exist, it creates and sets a new event loop.
    Returns the event loop for the current thread.
    """
    # Check if we're in the main thread
    is_main_thread = threading.current_thread() is threading.main_thread()
    
    try:
        # Try to get the existing event loop
        loop = asyncio.get_event_loop()
        
        # For the main thread, apply nest_asyncio if not already applied
        if is_main_thread and not hasattr(_thread_local, 'nest_asyncio_applied'):
            nest_asyncio.apply(loop)
            _thread_local.nest_asyncio_applied = True
            
        return loop
    except RuntimeError:
        # Create a new event loop if one doesn't exist
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # For the main thread, apply nest_asyncio
        if is_main_thread:
            nest_asyncio.apply(loop)
            _thread_local.nest_asyncio_applied = True
            
        return loop

# Check platform and set appropriate event loop policy for Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ensure the main thread has an event loop when this module is imported
ensure_event_loop() 