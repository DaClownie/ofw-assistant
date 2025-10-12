"""
Improved file upload handler with duplicate detection and immediate moving
"""
import hashlib
import shutil
import json
from pathlib import Path
from datetime import datetime


class FileHandler:
    """Handle file uploads with deduplication and state tracking"""
    
    def __init__(self, case_storage_path):
        """
        Initialize file handler
        
        Args:
            case_storage_path: Path to case storage directory (e.g., data/case_files/case_123)
        """
        self.case_storage_path = Path(case_storage_path)
        self.case_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Manifest file tracks all files in the case
        self.manifest_path = self.case_storage_path / ".manifest.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self):
        """Load or create manifest file"""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_manifest(self):
        """Save manifest file"""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def calculate_checksum(self, file_path):
        """
        Calculate SHA256 checksum of file
        
        Args:
            file_path: Path to file
            
        Returns:
            str: Hexadecimal checksum
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def is_duplicate(self, checksum, filename):
        """
        Check if file is a duplicate based on checksum
        
        Args:
            checksum: SHA256 checksum of file
            filename: Original filename
            
        Returns:
            tuple: (is_duplicate: bool, existing_filename: str or None)
        """
        for existing_file, info in self.manifest.items():
            if info.get('checksum') == checksum:
                return True, existing_file
        return False, None
    
    def get_unique_filename(self, filename):
        """
        Get unique filename if file already exists in case
        
        Args:
            filename: Original filename
            
        Returns:
            str: Unique filename
        """
        base_path = self.case_storage_path / filename
        
        if not base_path.exists() and filename not in self.manifest:
            return filename
        
        # File exists, add counter
        stem = base_path.stem
        suffix = base_path.suffix
        counter = 1
        
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = self.case_storage_path / new_name
            if not new_path.exists() and new_name not in self.manifest:
                return new_name
            counter += 1
    
    def add_file(self, source_path, original_filename, metadata=None):
        """
        Add file to case storage with duplicate detection
        
        Args:
            source_path: Path to source file (in uploads)
            original_filename: Original name of file
            metadata: Optional dict of metadata (tags, flags, etc.)
            
        Returns:
            dict: Result with status and information
        """
        source_path = Path(source_path)
        
        # Calculate checksum
        checksum = self.calculate_checksum(source_path)
        
        # Check for duplicates
        is_dup, existing_file = self.is_duplicate(checksum, original_filename)
        if is_dup:
            return {
                'status': 'duplicate',
                'message': f"File is a duplicate of '{existing_file}'",
                'existing_file': existing_file,
                'checksum': checksum
            }
        
        # Get unique filename
        unique_filename = self.get_unique_filename(original_filename)
        dest_path = self.case_storage_path / unique_filename
        
        try:
            # Move file from uploads to case storage
            shutil.move(str(source_path), str(dest_path))
            
            # Add to manifest
            self.manifest[unique_filename] = {
                'checksum': checksum,
                'original_name': original_filename,
                'added_date': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self._save_manifest()
            
            return {
                'status': 'success',
                'message': f"File added as '{unique_filename}'",
                'filename': unique_filename,
                'path': str(dest_path),
                'checksum': checksum,
                'was_renamed': unique_filename != original_filename
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to move file: {str(e)}",
                'error': str(e)
            }
    
    def get_file_info(self, filename):
        """Get information about a file in the manifest"""
        return self.manifest.get(filename)
    
    def list_files(self):
        """List all files in the case"""
        return list(self.manifest.keys())
    
    def get_duplicate_count(self):
        """Count files with same checksum (should be 0 after deduplication)"""
        checksums = [info['checksum'] for info in self.manifest.values()]
        return len(checksums) - len(set(checksums))


class ProcessingTracker:
    """Track file processing state to handle interruptions"""
    
    def __init__(self, case_id):
        """
        Initialize processing tracker
        
        Args:
            case_id: ID of the case being processed
        """
        self.case_id = case_id
        self.state_file = Path(f"data/.processing_state_{case_id}.json")
        self.state = self._load_state()
    
    def _load_state(self):
        """Load processing state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {'processed': [], 'failed': [], 'session_start': datetime.now().isoformat()}
        return {'processed': [], 'failed': [], 'session_start': datetime.now().isoformat()}
    
    def _save_state(self):
        """Save processing state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def is_processed(self, filename, checksum):
        """Check if file has been processed in this session"""
        for item in self.state['processed']:
            if item['filename'] == filename and item['checksum'] == checksum:
                return True
        return False
    
    def mark_processed(self, filename, checksum, result):
        """Mark file as processed"""
        self.state['processed'].append({
            'filename': filename,
            'checksum': checksum,
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
        self._save_state()
    
    def mark_failed(self, filename, error):
        """Mark file as failed"""
        self.state['failed'].append({
            'filename': filename,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()
    
    def get_summary(self):
        """Get processing summary"""
        return {
            'total_processed': len(self.state['processed']),
            'total_failed': len(self.state['failed']),
            'session_start': self.state['session_start']
        }
    
    def clear(self):
        """Clear processing state (call after successful batch)"""
        if self.state_file.exists():
            self.state_file.unlink()
        self.state = {'processed': [], 'failed': [], 'session_start': datetime.now().isoformat()}