import subprocess
import json

def tag_with_llama(text):
    prompt = f"Tag this text for issues related to parenting, diagnosis, and conflict: {text}"
    result = subprocess.run(
        ["ollama", "run", "llama3.1:8b", prompt],
        capture_output=True,
        text=True
    )
    output = result.stdout.strip()
    tags = [t.strip().lower() for t in output.split(",") if t.strip()]
    return tags
