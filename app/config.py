"""
Configuration constants and settings for OFW Assistant
"""
from pathlib import Path

# Environment and API
ENV_PATH = Path(".env")

# Tagging Configuration
KEY_PHRASES = ["court order", "emotional harm", "diagnosis", "manipulation", "parenting time"]
TOKEN_LIMIT = 1000  # adjustable threshold for GPT-4 usage

# File Paths
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
CASE_FILES_DIR = DATA_DIR / "case_files"

# Storage Paths
USER_STORAGE_PATH = Path.home() / "OFW_Assistant_Files"

# UI Configuration
PAGE_TITLE = "OFW Assistant"
PAGE_ICON = "📄"

# Supported File Types
SUPPORTED_FILE_TYPES = [
    "pdf", "docx", "txt", "eml", 
    "mp3", "m4a", 
    "jpg", "jpeg", "png", "heic", "tiff", "gif", "bmp",
    "mp4", "mov", "mkv", "avi"
]

# Custom CSS for scrollbar
SCROLLBAR_CSS = """
<style>
::-webkit-scrollbar {
    width: 12px;
}
::-webkit-scrollbar-thumb {
    background-color: #bbb;
    border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
    background: #888;
}
</style>
"""