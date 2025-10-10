"""
Local storage management component for sidebar
"""
import streamlit as st
import shutil
import platform
import subprocess
import time
from pathlib import Path
from app.config import USER_STORAGE_PATH, CASE_FILES_DIR


def render_storage_expander():
    """Render local storage management in sidebar expander"""
    with st.sidebar.expander("📁 Local Storage"):
        if st.button("📂 Open File Storage"):
            _open_file_storage()
        
        st.caption("⚠️ Note: Deleting local files will break memo generation functionality")


def _open_file_storage():
    """Open the local file storage directory in system file explorer"""
    # Create user-friendly storage location
    USER_STORAGE_PATH.mkdir(exist_ok=True)
    
    # Copy case files to user directory if they don't exist
    if CASE_FILES_DIR.exists():
        for case_folder in CASE_FILES_DIR.iterdir():
            if case_folder.is_dir():
                dest_folder = USER_STORAGE_PATH / case_folder.name
                if not dest_folder.exists():
                    shutil.copytree(case_folder, dest_folder)
    
    # Open the folder in file explorer
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(USER_STORAGE_PATH)])
        elif system == "Windows":
            subprocess.run(["explorer", str(USER_STORAGE_PATH)])
        else:  # Linux
            subprocess.run(["xdg-open", str(USER_STORAGE_PATH)])
        
        success_placeholder = st.sidebar.empty()
        success_placeholder.success("File storage opened!")
        time.sleep(2)
        success_placeholder.empty()
    except Exception as e:
        st.error(f"Could not open folder: {e}")
        st.code(f"Files are stored at: {USER_STORAGE_PATH}")