#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def create_installer():
    """Create a simple installer package"""
    
    # Create installer directory
    installer_dir = Path("OFW_Assistant_Installer")
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    installer_dir.mkdir()
    
    # Copy application files
    shutil.copytree("app", installer_dir / "app")
    shutil.copy("app.py", installer_dir)
    shutil.copy("requirements.txt", installer_dir)
    
    # Copy FFmpeg binary
    ffmpeg_dir = installer_dir / "binaries"
    ffmpeg_dir.mkdir()
    shutil.copy("binaries/ffmpeg", ffmpeg_dir)
    
    # Create install script
    install_script = """#!/bin/bash
echo "Installing OFW Assistant..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create installation directory
INSTALL_DIR="$HOME/Applications/OFW_Assistant"
mkdir -p "$INSTALL_DIR"

# Copy files from the installer directory
cp -r "$SCRIPT_DIR/app" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/binaries" "$INSTALL_DIR/"

# Create virtual environment
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python packages (this may take 5-10 minutes)..."
pip install -r requirements.txt

# Pre-download ML models to avoid first-run delays
echo "Downloading AI models (this may take several minutes)..."
python3 << 'PYEOF'
print("Downloading sentence transformer model...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Sentence transformer ready")

print("Downloading EasyOCR models...")
import easyocr
reader = easyocr.Reader(['en'])
print("EasyOCR ready")

print("Downloading Whisper model...")
import whisper
model = whisper.load_model("base")
print("Whisper ready")

print("All models downloaded successfully!")
PYEOF

# Create launcher script
cat > "$HOME/Applications/OFW_Assistant/launch.sh" << 'EOF'
#!/bin/bash

# Kill any existing Streamlit processes on port 8501
if lsof -ti:8501 >/dev/null 2>&1; then
    echo "Stopping existing OFW Assistant..."
    lsof -ti:8501 | xargs kill >/dev/null 2>&1
    sleep 2
fi

# Change to app directory
cd "$HOME/Applications/OFW_Assistant"

# Activate virtual environment
source venv/bin/activate

# Suppress warnings
export PYTHONWARNINGS="ignore::DeprecationWarning"
export TOKENIZERS_PARALLELISM="false"

# Start Streamlit
echo "Starting OFW Assistant..."
python -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false &

# Wait for server to start
sleep 3

# Open browser
open http://localhost:8501

echo ""
echo "OFW Assistant is running at http://localhost:8501"
echo "Processing files may take a moment - check your browser"
echo ""
echo "To stop: Close this terminal window or press Ctrl+C"
EOF

chmod +x "$HOME/Applications/OFW_Assistant/launch.sh"

# Create desktop shortcut that opens Terminal
cat > "$HOME/Desktop/OFW Assistant" << 'EOF'
#!/bin/bash
osascript -e 'tell application "Terminal" to do script "'"$HOME"'/Applications/OFW_Assistant/launch.sh"'
EOF

chmod +x "$HOME/Desktop/OFW Assistant"

echo "Installation complete!"
echo "Launch the app using the desktop shortcut or run:"
echo "$HOME/Applications/OFW_Assistant/launch.sh"
"""
    
    with open(installer_dir / "install.sh", "w") as f:
        f.write(install_script)
    
    os.chmod(installer_dir / "install.sh", 0o755)
    
    print(f"Installer created in {installer_dir}")
    print("Users run: ./install.sh")

if __name__ == "__main__":
    create_installer()