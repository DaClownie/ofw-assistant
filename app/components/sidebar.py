"""
Main sidebar component with navigation and settings
"""
import streamlit as st
from app.components.project_settings import render_settings_expander
from app.components.storage_manager import render_storage_expander
from app.components.api_key_manager import render_api_key_expander


def render_sidebar():
    """Render the complete sidebar with navigation and all components"""
    st.sidebar.title("OFW Assistant")
    
    # Main navigation
    page = st.sidebar.radio("Navigation", ["Upload", "Dashboard", "Memo Builder"])
    
    # Divider
    st.sidebar.markdown("---")
    
    # Project Settings
    render_settings_expander()
    
    # Local Storage
    render_storage_expander()
    
    # API Key Management
    render_api_key_expander()
    
    return page