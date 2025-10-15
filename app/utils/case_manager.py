"""
Case management utilities for operations like delete, rename, and export
"""
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from app.utils.memory import load_memory, save_memory, get_cases
from app.utils.controlled_taxonomy import controlled_taxonomy


class CaseManager:
    """Manage case operations like delete, rename, export"""
    
    def __init__(self):
        self.case_files_dir = Path("data/case_files")
        self.processing_state_dir = Path("data")
    
    def _normalize_case_id(self, case_id):
        """Normalize case ID to match folder name (replace spaces with underscores)"""
        return case_id.replace(" ", "_")
    
    def normalize_all_folders(self):
        """
        One-time migration: Rename all folders with spaces to use underscores
        
        Returns:
            dict: Results of migration
        """
        if not self.case_files_dir.exists():
            return {'renamed': 0, 'errors': [], 'already_normalized': 0}
        
        results = {
            'renamed': 0,
            'errors': [],
            'already_normalized': 0
        }
        
        for folder in self.case_files_dir.iterdir():
            if not folder.is_dir():
                continue
            
            folder_name = folder.name
            
            # Skip if already normalized (no spaces)
            if ' ' not in folder_name:
                results['already_normalized'] += 1
                continue
            
            # Calculate new name
            new_name = folder_name.replace(' ', '_')
            new_path = self.case_files_dir / new_name
            
            # Check if target already exists
            if new_path.exists():
                results['errors'].append(f"Cannot rename '{folder_name}' - '{new_name}' already exists")
                continue
            
            try:
                # Rename folder
                folder.rename(new_path)
                
                # Update memory.json
                memory = load_memory()
                for fname, meta in memory.items():
                    if meta.get('case_id') == folder_name:
                        meta['case_id'] = new_name
                save_memory(memory)
                
                results['renamed'] += 1
            except Exception as e:
                results['errors'].append(f"Failed to rename '{folder_name}': {str(e)}")
        
        return results
    
    def get_case_stats(self, case_id):
        """
        Get statistics for a case
        
        Args:
            case_id: Case identifier
            
        Returns:
            dict: Case statistics
        """
        memory = load_memory()
        case_files = [(fname, meta) for fname, meta in memory.items() 
                     if meta.get("case_id") == case_id]
        
        if not case_files:
            return {
                'exists': False,
                'file_count': 0,
                'transcript_count': 0,
                'flag_count': 0,
                'tags': [],
                'categories': {}
            }
        
        # Count stats
        transcript_count = sum(1 for fname, meta in case_files if meta.get("transcript"))
        flag_count = sum(len(meta.get("flags", [])) for fname, meta in case_files)
        
        # Collect tags
        all_tags = set()
        for fname, meta in case_files:
            all_tags.update(meta.get("tags", []))
        
        # Group by category
        categories = {}
        for tag in all_tags:
            cat = controlled_taxonomy.get_category_for_tag(tag)
            categories.setdefault(cat, []).append(tag)
        
        # Get creation date from folder
        case_path = self.case_files_dir / self._normalize_case_id(case_id)
        created_date = None
        if case_path.exists():
            created_date = datetime.fromtimestamp(case_path.stat().st_ctime).strftime('%Y-%m-%d')
        
        return {
            'exists': True,
            'file_count': len(case_files),
            'transcript_count': transcript_count,
            'flag_count': flag_count,
            'tags': list(all_tags),
            'categories': categories,
            'created_date': created_date,
            'files': case_files
        }
    
    def can_delete_case(self, case_id):
        """
        Check if case can be safely deleted
        
        Args:
            case_id: Case identifier
            
        Returns:
            tuple: (can_delete: bool, error_message: str or None)
        """
        import streamlit as st
        
        # Check if currently processing
        if st.session_state.get('is_processing'):
            return False, "Cannot delete - files are currently being processed"
        
        # Check if case exists
        case_path = self.case_files_dir / self._normalize_case_id(case_id)
        if not case_path.exists():
            return False, "Case folder not found"
        
        return True, None
    
    def delete_case(self, case_id):
        """
        Delete a case and all associated data
        
        Args:
            case_id: Case identifier
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if can delete
            can_delete, error_msg = self.can_delete_case(case_id)
            if not can_delete:
                return False, error_msg
            
            # Delete case folder
            case_path = self.case_files_dir / self._normalize_case_id(case_id)
            if case_path.exists():
                shutil.rmtree(case_path)
            
            # Clean memory.json
            memory = load_memory()
            updated_memory = {
                fname: meta for fname, meta in memory.items()
                if meta.get('case_id') != case_id
            }
            save_memory(updated_memory)
            
            # Delete processing state file if exists
            state_file = self.processing_state_dir / f".processing_state_{self._normalize_case_id(case_id)}.json"
            if state_file.exists():
                state_file.unlink()
            
            # Clean up empty parent directory if no cases left
            if self.case_files_dir.exists():
                remaining_items = list(self.case_files_dir.iterdir())
                # Only remove if completely empty (no folders or files)
                if len(remaining_items) == 0:
                    self.case_files_dir.rmdir()
            
            return True, f"Case '{case_id}' deleted successfully"
            
        except Exception as e:
            return False, f"Failed to delete case: {str(e)}"
    
    def rename_case(self, old_case_id, new_case_id):
        """
        Rename a case
        
        Args:
            old_case_id: Current case identifier
            new_case_id: New case identifier
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if new name already exists
            if new_case_id in get_cases():
                return False, f"Case '{new_case_id}' already exists"
            
            # Always use normalized folder names
            old_path = self.case_files_dir / self._normalize_case_id(old_case_id)
            new_path = self.case_files_dir / self._normalize_case_id(new_case_id)
            
            if not old_path.exists():
                return False, f"Case '{old_case_id}' not found"
            
            old_path.rename(new_path)
            
            # Update memory.json
            memory = load_memory()
            for fname, meta in memory.items():
                if meta.get('case_id') == old_case_id:
                    meta['case_id'] = new_case_id
            save_memory(memory)
            
            # Rename processing state file if exists
            old_state = self.processing_state_dir / f".processing_state_{old_case_id}.json"
            new_state = self.processing_state_dir / f".processing_state_{new_case_id}.json"
            if old_state.exists():
                old_state.rename(new_state)
            
            return True, f"Case renamed from '{old_case_id}' to '{new_case_id}'"
            
        except Exception as e:
            return False, f"Failed to rename case: {str(e)}"
    
    def export_case(self, case_id, output_path=None, include_manifest=True):
        """
        Export entire case to zip file
        
        Args:
            case_id: Case identifier
            output_path: Optional output path, defaults to downloads
            include_manifest: Include manifest file in zip
            
        Returns:
            tuple: (success: bool, path: str or None, message: str)
        """
        try:
            stats = self.get_case_stats(case_id)
            if not stats['exists']:
                return False, None, f"Case '{case_id}' not found"
            
            # Create output path
            if output_path is None:
                downloads_dir = Path.home() / "Downloads" / "ofw"
                downloads_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = downloads_dir / f"{case_id}_complete_{timestamp}.zip"
            
            # Create zip
            case_path = self.case_files_dir / self._normalize_case_id(case_id)
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files
                for file_path in case_path.rglob('*'):
                    if file_path.is_file() and file_path.name != '.manifest.json':
                        arcname = file_path.relative_to(case_path)
                        zipf.write(file_path, arcname)
                
                # Add manifest if requested
                if include_manifest:
                    manifest_content = self._generate_manifest(case_id, stats)
                    zipf.writestr('MANIFEST.txt', manifest_content)
            
            return True, str(output_path), f"Exported {stats['file_count']} files"
            
        except Exception as e:
            return False, None, f"Failed to export case: {str(e)}"
    
    def export_by_category(self, case_id, category, output_path=None):
        """
        Export files from a specific category
        
        Args:
            case_id: Case identifier
            category: Category name
            output_path: Optional output path
            
        Returns:
            tuple: (success: bool, path: str or None, message: str)
        """
        try:
            memory = load_memory()
            case_files = [(fname, meta) for fname, meta in memory.items() 
                         if meta.get("case_id") == case_id]
            
            # Filter by category
            category_files = []
            for fname, meta in case_files:
                for tag in meta.get("tags", []):
                    if controlled_taxonomy.get_category_for_tag(tag) == category:
                        category_files.append((fname, meta))
                        break
            
            if not category_files:
                return False, None, f"No files found in category '{category}'"
            
            # Create output path
            if output_path is None:
                downloads_dir = Path.home() / "Downloads" / "ofw"
                downloads_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_category = category.replace(' ', '_')
                output_path = downloads_dir / f"{case_id}_{safe_category}_{timestamp}.zip"
            
            # Create zip
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fname, meta in category_files:
                    file_path = Path(meta.get('path', ''))
                    if file_path.exists():
                        zipf.write(file_path, fname)
                
                # Add manifest
                manifest = f"Export: {case_id} - {category}\n"
                manifest += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                manifest += f"Files: {len(category_files)}\n\n"
                for fname, meta in category_files:
                    manifest += f"{fname}\n"
                    manifest += f"  Tags: {', '.join(meta.get('tags', []))}\n"
                    if meta.get('flags'):
                        manifest += f"  Flags: {', '.join(meta.get('flags', []))}\n"
                    manifest += "\n"
                zipf.writestr('MANIFEST.txt', manifest)
            
            return True, str(output_path), f"Exported {len(category_files)} files from {category}"
            
        except Exception as e:
            return False, None, f"Failed to export by category: {str(e)}"
    
    def export_by_tags(self, case_id, tags, output_path=None):
        """
        Export files matching specific tags
        
        Args:
            case_id: Case identifier
            tags: List of tag names to match
            output_path: Optional output path
            
        Returns:
            tuple: (success: bool, path: str or None, message: str)
        """
        try:
            memory = load_memory()
            case_files = [(fname, meta) for fname, meta in memory.items() 
                         if meta.get("case_id") == case_id]
            
            # Filter by tags (ANY match)
            matching_files = []
            for fname, meta in case_files:
                file_tags = set(meta.get("tags", []))
                if file_tags.intersection(set(tags)):
                    matching_files.append((fname, meta))
            
            if not matching_files:
                return False, None, f"No files found with tags: {', '.join(tags)}"
            
            # Create output path
            if output_path is None:
                downloads_dir = Path.home() / "Downloads" / "ofw"
                downloads_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                tag_label = "_".join(tags[:2])  # Use first 2 tags in filename
                if len(tags) > 2:
                    tag_label += "_plus"
                output_path = downloads_dir / f"{case_id}_{tag_label}_{timestamp}.zip"
            
            # Create zip with organized structure
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fname, meta in matching_files:
                    file_path = Path(meta.get('path', ''))
                    if file_path.exists():
                        zipf.write(file_path, f"files/{fname}")
                
                # Add detailed manifest
                manifest = f"Export: {case_id}\n"
                manifest += f"Filtered by tags: {', '.join(tags)}\n"
                manifest += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                manifest += f"Total files: {len(matching_files)}\n\n"
                manifest += "=" * 50 + "\n\n"
                
                for fname, meta in matching_files:
                    manifest += f"{fname}\n"
                    manifest += f"  Tags: {', '.join(meta.get('tags', []))}\n"
                    if meta.get('flags'):
                        manifest += f"  Flags: {', '.join(meta.get('flags', []))}\n"
                    manifest += "\n"
                
                zipf.writestr('MANIFEST.txt', manifest)
            
            return True, str(output_path), f"Exported {len(matching_files)} files matching {len(tags)} tag(s)"
            
        except Exception as e:
            return False, None, f"Failed to export by tags: {str(e)}"
    
    def _generate_manifest(self, case_id, stats):
        """Generate manifest content for case export"""
        manifest = f"Case Export: {case_id}\n"
        manifest += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        manifest += f"Total files: {stats['file_count']}\n"
        manifest += f"Files with transcripts: {stats['transcript_count']}\n"
        manifest += f"Total flags: {stats['flag_count']}\n\n"
        manifest += "=" * 50 + "\n\n"
        
        # List files
        manifest += "FILES:\n\n"
        for fname, meta in stats['files']:
            manifest += f"{fname}\n"
            if meta.get('tags'):
                manifest += f"  Tags: {', '.join(meta.get('tags', []))}\n"
            if meta.get('flags'):
                manifest += f"  Flags: {', '.join(meta.get('flags', []))}\n"
            manifest += "\n"
        
        return manifest