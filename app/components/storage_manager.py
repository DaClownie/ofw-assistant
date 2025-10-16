"""
Local storage management component for sidebar
"""
import streamlit as st
import platform
import subprocess
import time
from pathlib import Path
from app.config import CASE_FILES_DIR


def render_storage_expander():
    """Render local storage management in sidebar expander"""
    with st.sidebar.expander("📁 Local Storage"):
        if st.button("📂 Open File Storage"):
            _open_file_storage()
        
        st.caption("⚠️ Note: Deleting local files will break memo generation functionality")


def _open_file_storage():
    """Open the case files directory in system file explorer"""
    # Ensure the directory exists
    CASE_FILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Open the folder in file explorer
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(CASE_FILES_DIR)])
        elif system == "Windows":
            subprocess.run(["explorer", str(CASE_FILES_DIR)])
        else:  # Linux
            subprocess.run(["xdg-open", str(CASE_FILES_DIR)])
        
        success_placeholder = st.sidebar.empty()
        success_placeholder.success("File storage opened!")
        time.sleep(2)
        success_placeholder.empty()
    except Exception as e:
        st.error(f"Could not open folder: {e}")
        st.code(f"Files are stored at: {CASE_FILES_DIR}")