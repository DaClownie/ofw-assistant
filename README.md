# OFW Assistant

An AI-powered document analysis tool designed for family law professionals to analyze case files, detect patterns related to DSM-5 criteria, and generate professional memos.

## Features

- **Multi-format Support**: Process PDFs, DOCX, images (OCR), audio, and video files
- **Intelligent Tagging**: Automatic categorization using 111+ controlled taxonomy tags across 13 categories
- **Pattern Detection**: Identifies concerning patterns including safety issues, fabricated symptoms, and parental alienation indicators
- **AI-Powered Memos**: Generate professional case memos using GPT-4
- **Case Management**: Organize files by case with advanced search and filtering
- **Audio/Video Transcription**: Automatic transcription using OpenAI Whisper
- **Privacy-First**: All processing happens locally on your machine

## Screenshots

_(Add screenshots here after testing)_

## Installation

### Requirements

- macOS 10.15 or later
- Python 3.10 or higher (3.11+ recommended)
- OpenAI API key
- FFmpeg (bundled in installer)

### Quick Install

1. Download the latest DMG from [Releases](https://github.com/daclownie/ofw-assistant/releases)
2. Mount the DMG and copy `OFW_Assistant_Installer` to your Desktop
3. Open Terminal and run:

```bash
   cd ~/Desktop/OFW_Assistant_Installer
   ./install.sh
```

4. Wait for installation (5-10 minutes for dependencies and AI models)
5. Launch from Desktop shortcut or:

```bash
    ~/Applications/OFW_Assistant/launch.sh
```

### Development Setup

# Clone the repository

git clone https://github.com/your-username/ofw-assistant.git
cd ofw-assistant

# Create virtual environment

python3 -m venv venv
source venv/bin/activate

# Install dependencies

pip install -r requirements.txt

# Run the application

streamlit run app.py

### Building a Release

```bash
    ./release.sh
```

This will:

1. Prompt for version update and changelog
2. Create installer package
3. Generate DMG for distribution

### Usage

# Uploading Files

1. Select or create a case
2. Upload documents (drag & drop or file picker)
3. Files are automatically analyzed and tagged

# Creating Memos

1. Navigate to Memo Builder
2. Select files by case or individually
3. Generate base memo or enhance with AI
4. Export as .txt or .docx

# Dashboard

- Browse by category or case
- Search across all content
- View analytics and flag summaries

### Tech Stack

- **Frontend:** Streamlit
- **AI Models:**
  - OpenAI GPT-4 (memo generation, complex tagging)
  - LLaMA 3.1 (local tagging)
  - EasyOCR (image text extraction)
  - OpenAI Whisper (audio transcription)
- **Vector Storage:** ChromaDB with Sentence Transformers
- **Document Processing:** LangChain, PyPDF, python-docx

### Privacy & Data

- All AI processing uses your own API key
- Files stored locally in ~/OFW_Assistant_Files/
- No data sent to third parties except OpenAI API (when using GPT-4 features)
- Case files organized by case ID for easy management

### Contributing

Contributions welcome! Please see TODO.md for planned features and improvements.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### License

This project is licensed under the MIT License - see the LICENSE file for details.

### Support

For issues or questions, please open an issue on GitHub.

Note: This tool is designed to assist legal professionals in document analysis. It should not be used as a substitute for professional legal judgment or mental health diagnosis.
