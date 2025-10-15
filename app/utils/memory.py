import json
from pathlib import Path

MEMORY_PATH = Path("data/memory.json")
MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)

def update_memory(file_path, tags, case_id=None, flags=None, transcript=None, extra_meta=None):
    memory = {}
    if MEMORY_PATH.exists():
        with open(MEMORY_PATH, "r") as f:
            memory = json.load(f)
    memory[file_path] = {
        "tags": tags,
        "case_id": case_id,
        "flags": flags or [],
        "transcript": transcript,  # store transcript text if audio
        "path": file_path
    }
    if extra_meta:
        memory[file_path].update(extra_meta)
        
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)

def load_memory():
    if not MEMORY_PATH.exists():
        return {}
    with open(MEMORY_PATH, "r") as f:
        return json.load(f)

def save_memory(memory):
    """
    Save memory dictionary to file
    
    Args:
        memory: Dictionary of file metadata to save
    """
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)

def get_cases():
    memory = load_memory()
    cases = set()
    for meta in memory.values():
        if meta.get("case_id"):
            cases.add(meta["case_id"])
    return sorted(cases)