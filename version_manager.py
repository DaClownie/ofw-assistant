#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

VERSION_FILE = Path("version.json")
CHANGELOG_FILE = Path("CHANGELOG.md")

def load_version():
    """Load current version from file"""
    if VERSION_FILE.exists():
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    return {"version": "1.0.0", "build": 1}

def save_version(version_data):
    """Save version to file"""
    with open(VERSION_FILE, 'w') as f:
        json.dump(version_data, f, indent=2)

def increment_version(version_type='patch'):
    """Increment version number"""
    version_data = load_version()
    major, minor, patch = map(int, version_data['version'].split('.'))
    
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    version_data['version'] = f"{major}.{minor}.{patch}"
    version_data['build'] += 1
    version_data['date'] = datetime.now().isoformat()
    
    return version_data

def add_changelog_entry(version, changes):
    """Add entry to changelog"""
    if not CHANGELOG_FILE.exists():
        CHANGELOG_FILE.write_text("# Changelog\n\n")
    
    with open(CHANGELOG_FILE, 'r') as f:
        existing = f.read()
    
    date = datetime.now().strftime('%Y-%m-%d')
    entry = f"## [{version}] - {date}\n\n"
    
    for change_type, items in changes.items():
        if items:
            entry += f"### {change_type}\n"
            for item in items:
                entry += f"- {item}\n"
            entry += "\n"
    
    # Insert after the header
    parts = existing.split('\n\n', 1)
    new_content = parts[0] + '\n\n' + entry
    if len(parts) > 1:
        new_content += parts[1]
    
    CHANGELOG_FILE.write_text(new_content)

def prompt_for_version():
    """Interactive version update"""
    print("Current version:", load_version()['version'])
    print("\nWhat type of update is this?")
    print("1. Patch (bug fixes, minor changes) - x.x.X")
    print("2. Minor (new features, backwards compatible) - x.X.0")
    print("3. Major (breaking changes) - X.0.0")
    
    choice = input("\nEnter choice (1-3): ").strip()
    version_types = {'1': 'patch', '2': 'minor', '3': 'major'}
    version_type = version_types.get(choice, 'patch')
    
    new_version = increment_version(version_type)
    
    print(f"\nNew version will be: {new_version['version']}")
    
    # Collect changelog entries
    print("\nEnter changes (press Enter on empty line when done):")
    
    changes = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }
    
    for change_type in changes.keys():
        print(f"\n{change_type}:")
        while True:
            entry = input("  - ").strip()
            if not entry:
                break
            changes[change_type].append(entry)
    
    # Confirm
    print(f"\n{'='*50}")
    print(f"Version: {new_version['version']}")
    print(f"Build: {new_version['build']}")
    for change_type, items in changes.items():
        if items:
            print(f"\n{change_type}:")
            for item in items:
                print(f"  - {item}")
    
    confirm = input(f"\n{'='*50}\nProceed with this version? (y/n): ").strip().lower()
    
    if confirm == 'y':
        save_version(new_version)
        add_changelog_entry(new_version['version'], changes)
        print(f"\n✅ Version updated to {new_version['version']}")
        return new_version
    else:
        print("❌ Version update cancelled")
        return None

if __name__ == "__main__":
    prompt_for_version()