"""
Project settings component for sidebar
"""
import streamlit as st
from app.utils.project_settings import load_project_settings, save_project_settings


def render_settings_expander():
    """Render AI instructions settings in sidebar expander"""
    with st.sidebar.expander("⚙️ AI Instructions"):
        settings = load_project_settings()
        
        instructions = st.text_area(
            "AI Analysis Instructions:",
            value=settings.get("instructions", ""),
            height=300,
            help="These instructions guide all AI analysis and memo generation"
        )
        
        if st.button("Save Instructions"):
            save_project_settings({"instructions": instructions})
            st.success("Instructions saved!")