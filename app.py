"""
OFW Assistant - Main Application Entry Point
Refactored for better maintainability and modularity
"""
import os
import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings('ignore', category=NotOpenSSLWarning)

# Suppress all warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings('ignore')

import streamlit as st

try:
    import torch
    torch._classes = {}
except:
    pass

# Import configuration and components
from app.config import PAGE_TITLE, PAGE_ICON, SCROLLBAR_CSS
from app.components.api_key_manager import ensure_api_key
from app.components.sidebar import render_sidebar
from app.utils.memory import load_memory

# Import page modules
from app.pages.upload import render_upload_page
from app.pages.dashboard import render_dashboard_page
from app.pages.memo_builder import render_memo_builder_page
from app.pages.case_management import render_case_management_page


def main():
    """Main application entry point"""
    # Page configuration
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    
    # Apply custom CSS
    st.markdown(SCROLLBAR_CSS, unsafe_allow_html=True)
    
    # Ensure API key is configured
    ensure_api_key()
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Load memory once for all pages
    memory = load_memory()
    
    # Route to appropriate page
    if page == "Upload":
        render_upload_page()
    elif page == "Dashboard":
        render_dashboard_page(memory)
    elif page == "Memo Builder":
        render_memo_builder_page(memory)
    elif page == "Case Management":
        render_case_management_page()


if __name__ == "__main__":
    main()