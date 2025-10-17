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
echo "================================================"
echo "OFW Assistant Installer"
echo "================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Define installation directory
INSTALL_DIR="$HOME/Applications/OFW_Assistant"

# Initialize flags
KEEP_DATA=false
KEEP_VENV=false

# Check if previous installation exists
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Existing installation detected"
    echo ""
    echo "Choose installation type:"
    echo "  [1] Clean Install - Remove everything and start fresh"
    echo "  [2] Update - Keep data and dependencies, update app only (FAST)"
    echo "  [3] Cancel"
    echo ""
    read -p "Enter choice (1/2/3): " install_choice
    
    case $install_choice in
        1)
            echo ""
            echo "🧹 Performing clean installation..."
            echo ""
            
            # Remove entire installation
            echo "🗑️  Removing old installation..."
            rm -rf "$INSTALL_DIR"
            
            # Remove old duplicate files location (from versions before storage_manager fix)
            if [ -d "$HOME/OFW_Assistant_Files" ]; then
                echo "🗑️  Removing old duplicate files location..."
                rm -rf "$HOME/OFW_Assistant_Files"
            fi
            
            echo "✅ Clean installation preparation complete"
            ;;
        2)
            echo ""
            echo "⚡ Performing fast update..."
            echo ""
            
            # Backup data folder
            if [ -d "$INSTALL_DIR/data" ]; then
                echo "💾 Preserving data folder..."
                mkdir -p /tmp/ofw_backup
                cp -r "$INSTALL_DIR/data" /tmp/ofw_backup/
                KEEP_DATA=true
            fi
            
            # Backup venv folder
            if [ -d "$INSTALL_DIR/venv" ]; then
                echo "💾 Preserving Python environment..."
                mkdir -p /tmp/ofw_backup
                cp -r "$INSTALL_DIR/venv" /tmp/ofw_backup/
                KEEP_VENV=true
            fi
            
            # Remove only app code
            echo "🔄 Removing old app files..."
            rm -rf "$INSTALL_DIR/app"
            rm -f "$INSTALL_DIR/app.py"
            rm -f "$INSTALL_DIR/requirements.txt"
            rm -rf "$INSTALL_DIR/binaries"
            
            echo "✅ Ready for update"
            ;;
        3|*)
            echo "Installation cancelled."
            exit 0
            ;;
    esac
    echo ""
else
    echo "No previous installation found. Proceeding with fresh install..."
    echo ""
fi

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy files from the installer directory
echo "📂 Installing application files..."
cp -r "$SCRIPT_DIR/app" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/binaries" "$INSTALL_DIR/"

# Restore backed up data if it exists
if [ "$KEEP_DATA" = true ]; then
    echo "📦 Restoring data folder..."
    cp -r /tmp/ofw_backup/data "$INSTALL_DIR/"
fi

if [ "$KEEP_VENV" = true ]; then
    echo "📦 Restoring Python environment..."
    cp -r /tmp/ofw_backup/venv "$INSTALL_DIR/"
fi

# Clean up backup
if [ -d "/tmp/ofw_backup" ]; then
    rm -rf /tmp/ofw_backup
fi

cd "$INSTALL_DIR"

# Handle Python environment
if [ "$KEEP_VENV" = true ]; then
    echo "🐍 Updating Python packages..."
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✅ Dependencies updated"
else
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing Python packages (this may take 5-10 minutes)..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✅ Dependencies installed"
fi

# Check for AI models and download only if missing
echo "🤖 Checking AI models..."
python3 << 'PYEOF'
import sys
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

models_to_download = []

# Check Sentence Transformers (in HuggingFace cache)
hf_cache = Path.home() / ".cache/huggingface"
if not hf_cache.exists() or not any(hf_cache.rglob("*MiniLM*")):
    models_to_download.append("sentence-transformers")

# Check EasyOCR
easyocr_cache = Path.home() / ".EasyOCR/model"
if not easyocr_cache.exists() or not list(easyocr_cache.glob("*.pth")):
    models_to_download.append("easyocr")

# Check Whisper
whisper_cache = Path.home() / ".cache/whisper"
if not whisper_cache.exists() or not list(whisper_cache.glob("*.pt")):
    models_to_download.append("whisper")

if models_to_download:
    print(f"  → Downloading missing models: {', '.join(models_to_download)}")
    print("  (This may take several minutes...)")
    
    if "sentence-transformers" in models_to_download:
        print("    • Sentence Transformers...", end=" ", flush=True)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓")
    
    if "easyocr" in models_to_download:
        print("    • EasyOCR...", end=" ", flush=True)
        import easyocr
        reader = easyocr.Reader(['en'], verbose=False)
        print("✓")
    
    if "whisper" in models_to_download:
        print("    • Whisper...", end=" ", flush=True)
        import whisper
        model = whisper.load_model("base")
        print("✓")
    
    print("✅ Models downloaded successfully!")
else:
    print("✅ All models already cached - skipping download")

PYEOF

# Create launcher script
cat > "$INSTALL_DIR/launch.sh" << 'EOF'
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

chmod +x "$INSTALL_DIR/launch.sh"

# Create desktop shortcut that opens Terminal
cat > "$HOME/Desktop/OFW Assistant.command" << 'EOF'
#!/bin/bash
osascript -e 'tell application "Terminal" to do script "'"$HOME"'/Applications/OFW_Assistant/launch.sh"'
EOF

chmod +x "$HOME/Desktop/OFW Assistant.command"

echo ""
echo "================================================"
echo "✅ Installation complete!"
echo "================================================"
echo ""
echo "Launch the app using:"
echo "  • Desktop shortcut: 'OFW Assistant.command'"
echo "  • Or run: $HOME/Applications/OFW_Assistant/launch.sh"
echo ""
"""
    
    with open(installer_dir / "install.sh", "w") as f:
        f.write(install_script)
    
    os.chmod(installer_dir / "install.sh", 0o755)
    
    print(f"Installer created in {installer_dir}")
    print("Users run: ./install.sh")

if __name__ == "__main__":
    create_installer()