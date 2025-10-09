# app/utils/audio.py
import whisper
import subprocess
import tempfile
import os
import sys
from pathlib import Path

def get_ffmpeg_path():
    """Get path to bundled ffmpeg binary"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        return str(bundle_dir / "ffmpeg")
    else:
        # Running in development - use system ffmpeg
        return "ffmpeg"

AUDIO_TMP_DIR = Path("data/audio_tmp")
AUDIO_TMP_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi"]

def extract_audio_with_ffmpeg(video_path: str) -> str:
    """
    Extracts audio from a video file using ffmpeg and returns the path to the audio file.
    """
    ffmpeg_cmd = get_ffmpeg_path()  # Use bundled ffmpeg
    output_path = AUDIO_TMP_DIR / (Path(video_path).stem + "_extracted.mp3")
    command = [
        ffmpeg_cmd,  # Changed from "ffmpeg" to use bundled version
        "-y",  # Overwrite if exists
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        str(output_path)
    ]
    subprocess.run(command, check=True, capture_output=True)
    return str(output_path)

def transcribe_audio(path: str) -> str:
    """
    Transcribes audio or video using local Whisper.
    For video files, it first extracts audio before transcription.
    """
    try:
        # Check if ffmpeg is available
        ffmpeg_cmd = get_ffmpeg_path()
        subprocess.run([ffmpeg_cmd, "-version"], check=True, capture_output=True)

        is_video = Path(path).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        audio_path = extract_audio_with_ffmpeg(path) if is_video else path

        # Load Whisper model
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        transcript = result["text"]

        # Delete temp audio if extracted
        if is_video and Path(audio_path).exists():
            try:
                Path(audio_path).unlink()
            except Exception as e:
                print(f"⚠️ Failed to delete temporary audio file: {e}")

        return transcript

    except FileNotFoundError:
        print("⚠️ ffmpeg not found. Please install ffmpeg or bundle it with your app.")
        return "[Error: ffmpeg not found — transcript unavailable.]"
    
    except subprocess.CalledProcessError as e:
        print(f"⚠️ ffmpeg failed: {e.stderr.decode().strip()}")
        return "[Error: failed to extract audio from video.]"

    except Exception as e:
        print(f"⚠️ Error transcribing audio: {e}")
        return "[Error during transcription.]"
