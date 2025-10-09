#!/usr/bin/env python3
import shutil
import subprocess
from pathlib import Path
from version_manager import load_version

def create_distribution_package():
    """Create final distribution package"""
    
    # Get current version
    version_data = load_version()
    version = version_data['version']
    
    # Create a clean distribution directory
    dist_name = f"OFW_Assistant_v{version}"
    dist_dir = Path(dist_name)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Copy the installer
    shutil.copytree("OFW_Assistant_Installer", dist_dir / "OFW_Assistant_Installer")
    
    # Copy changelog
    if Path("CHANGELOG.md").exists():
        shutil.copy("CHANGELOG.md", dist_dir / "CHANGELOG.md")
    
    # Create user instructions
    readme = """# OFW Assistant Installation

## Requirements

- macOS 10.15 or later
- Python 3.9 or higher
- Internet connection for downloading dependencies

## Installing Python (if needed)

Check if you have Python 3.9+ installed by opening Terminal and typing:

    python3 --version

If you see "Python 3.9.x" or higher, you're ready to install.

If not, install Python using one of these methods:

### Option 1: Official Python Installer (Recommended)

1. Visit https://www.python.org/downloads/
2. Download Python 3.11 or later for macOS
3. Run the installer and follow the prompts

### Option 2: Using Homebrew (if you have it)

Open Terminal and type:

    brew install python@3.11

## Installation (Choose one method)
1. Double-click the DMG file
2. Copy "OFW_Assistant_Installer" folder to your Desktop
then...

### Method 1: Finder Installation
3. Navigate to the "OFW_Assistant_Installer" folder on your desktop
4. Right-click on "install.sh" and select "Open With" > "Terminal"
5. Follow the installation prompts

### Method 2: Terminal Installation  
3. Open Terminal
4. Type: cd ~/Desktop/OFW_Assistant_Installer
5. Type: ./install.sh
6. Wait for installation to complete

## Running the Application

- Double-click the "OFW Assistant" icon on your Desktop, OR
- Run in Terminal: ~/Applications/OFW_Assistant/launch.sh

## First Time Setup

1. Enter your OpenAI API key when prompted
2. The app will open in your web browser
3. Start uploading and analyzing your files

## Troubleshooting

- If you get "permission denied" errors, try: chmod +x install.sh
- If Python commands fail, ensure Python 3.9+ is installed
- For "command not found" errors, restart Terminal after installing Python

## Support

The application creates case-organized folders in:
~/OFW_Assistant_Files/
"""

    
    with open(dist_dir / "README.md", "w") as f:
        f.write(readme)
    
    # Create DMG (Mac disk image)
    try:
        dmg_name = f"{dist_name}.dmg"
        subprocess.run([
            "hdiutil", "create",
            "-volname", "OFW Assistant",
            "-srcfolder", str(dist_dir),
            "-ov", "-format", "UDZO",
            dmg_name
        ], check=True)
        
        print(f"Distribution package created: {dmg_name}")
        print("Users can download this DMG file and follow the README instructions")
        
        # Also create ZIP as backup
        shutil.make_archive(dist_name, 'zip', dist_dir)
        print(f"ZIP backup created: {dist_name}.zip")
        
    except subprocess.CalledProcessError:
        # Fallback to ZIP if DMG creation fails
        shutil.make_archive(dist_name, 'zip', dist_dir)
        print(f"Distribution package created: {dist_name}.zip")
    
    # Cleanup temp directory
    shutil.rmtree(dist_dir)
    
    print(f"\n📦 Ready to distribute version {version}")
    
if __name__ == "__main__":
    create_distribution_package()