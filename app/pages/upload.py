"""
Upload page for document and media file processing
"""
import shutil
import streamlit as st
from pathlib import Path
from datetime import datetime
from app.config import UPLOADS_DIR, SUPPORTED_FILE_TYPES
from app.utils.memory import get_cases, update_memory


def render_upload_page():
    """Render the upload page UI and logic"""
    st.header("📤 Upload Documents or Audio")
    
    # Case selection
    case_id = _render_case_selector()
    
    if not case_id:
        st.warning("⚠️ Please select or create a case before uploading.")
        return
    
    # File upload and processing
    _render_file_uploader(case_id)


def _display_processing_summary(stats, total_files):
    """Display processing summary with stats"""
    st.markdown("---")
    st.subheader("📊 Processing Complete")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Files", total_files)
    col2.metric("Processed", stats['processed'], delta=None if stats['processed'] == total_files else f"{stats['processed'] - total_files}")
    col3.metric("Duplicates Skipped", stats['skipped_duplicates'])
    col4.metric("Errors", stats['errors'], delta=None if stats['errors'] == 0 else f"+{stats['errors']}")
    
    if stats['renamed'] > 0:
        st.info(f"ℹ️ {stats['renamed']} file(s) were renamed to avoid name collisions")
    
    if stats['skipped_duplicates'] > 0:
        st.info(f"ℹ️ {stats['skipped_duplicates']} duplicate file(s) were skipped")
    
    if stats['errors'] > 0:
        st.error(f"⚠️ {stats['errors']} file(s) failed to process. Check logs above for details.")
    else:
        st.success("✅ All files processed successfully!")


def _render_case_selector():
    """Render case selection/creation dropdown"""
    existing_cases = get_cases()
    case_options = ["-- Select existing case --"] + existing_cases + ["+ Create new case"]
    
    selected_option = st.selectbox("📁 Select or create a case:", case_options)
    
    if selected_option == "-- Select existing case --":
        st.info("👆 Please select an existing case or create a new one")
        return None
    elif selected_option == "+ Create new case":
        case_id_input = st.text_input("Enter new case ID:")
        if not case_id_input:
            st.warning("⚠️ Please enter a case ID for the new case")
            return None
        
        # Normalize case ID (replace spaces with underscores)
        case_id = case_id_input.replace(" ", "_")
        
        # Show normalization if it changed
        if case_id != case_id_input:
            st.info(f"ℹ️ Case ID folder name normalized: `{case_id_input}` → `{case_id}`")
        
        return case_id
    else:
        st.success(f"📂 Selected case: {selected_option}")
        return selected_option


def _render_file_uploader(case_id):
    """Render file uploader and process uploaded files"""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if currently processing
    is_processing = st.session_state.get('is_processing', False)
    
    # Disable uploader while processing
    uploaded_files = st.file_uploader(
        "Upload a document", 
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        disabled=is_processing,
        help="Upload files for processing. Files are checked for duplicates and processed individually." if not is_processing else "Processing in progress..."
    )
    
    if uploaded_files and not is_processing:
        _process_uploaded_files(uploaded_files, case_id)


def _process_uploaded_files(uploaded_files, case_id):
    """Process each uploaded file with duplicate detection and immediate moving"""
    from app.utils.file_handler import FileHandler, ProcessingTracker
    
    # Set processing flag
    st.session_state['is_processing'] = True
    
    # Initialize handlers
    case_storage_path = Path(f"data/case_files/{case_id}")
    file_handler = FileHandler(case_storage_path)
    tracker = ProcessingTracker(case_id)
    
    # Stats
    stats = {
        'processed': 0,
        'skipped_duplicates': 0,
        'errors': 0,
        'renamed': 0
    }
    
    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(uploaded_files)
    
    for idx, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (idx + 1) / total_files
        progress_bar.progress(progress)
        status_text.text(f"Processing {idx + 1}/{total_files}: {uploaded_file.name}")
        
        upload_path = UPLOADS_DIR / uploaded_file.name
        
        try:
            # Save uploaded file to temp location
            with open(upload_path, "wb") as f:
                shutil.copyfileobj(uploaded_file, f)
            
            # Calculate checksum before processing
            checksum = file_handler.calculate_checksum(upload_path)
            
            # Check if already processed in this session
            if tracker.is_processed(uploaded_file.name, checksum):
                st.info(f"⏭️ Skipping {uploaded_file.name} - already processed in this session")
                stats['processed'] += 1
                upload_path.unlink()  # Clean up temp file
                continue
            
            # Check for duplicates in case storage
            is_dup, existing_file = file_handler.is_duplicate(checksum, uploaded_file.name)
            if is_dup:
                st.warning(f"🔄 Skipping {uploaded_file.name} - duplicate of existing file: {existing_file}")
                stats['skipped_duplicates'] += 1
                upload_path.unlink()  # Clean up temp file
                tracker.mark_processed(uploaded_file.name, checksum, {'status': 'duplicate', 'existing_file': existing_file})
                continue
            
            # Process file with unified processor (it will move the file)
            result = _process_file_with_ai(upload_path, uploaded_file.name, case_id, checksum, file_handler)
            
            # Track as processed
            tracker.mark_processed(uploaded_file.name, checksum, result)
            stats['processed'] += 1
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            stats['errors'] += 1
            tracker.mark_failed(uploaded_file.name, str(e))
            
            # Clean up temp file if it exists
            if upload_path.exists():
                upload_path.unlink()
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display summary
    _display_processing_summary(stats, total_files)
    
    # Clear processing state
    tracker.clear()
    st.session_state['is_processing'] = False


def _process_file_with_ai(upload_path, filename, case_id, checksum, file_handler):
    """Process file using unified processor (which handles moving the file)"""
    from app.utils.unified_processor import FileProcessor
    from app.utils.controlled_smart_tagger import controlled_smart_tagger
    
    processor = FileProcessor()
    
    with st.spinner(f"🔄 Analyzing {filename}..."):
        # Process file (unified_processor handles the moving)
        result = processor.process_file(str(upload_path), case_id)
    
    # Update manifest with checksum for future duplicate detection
    # (File was already moved by unified_processor)
    file_handler.manifest[filename] = {
        'checksum': checksum,
        'original_name': filename,
        'added_date': datetime.now().isoformat(),
        'metadata': {
            'tags': result['tags'],
            'flags': result['flags'],
            'transcript': result.get('transcript')
        }
    }
    file_handler._save_manifest()
    
    st.success(f"✅ Processed: {filename}")
    
    # Display tags by category
    categorized = controlled_smart_tagger.get_tag_categories(result['tags'])
    
    tag_display = []
    for category, tags in categorized.items():
        if tags:
            tag_display.append(f"**{category.replace('_', ' ').title()}:** {', '.join(tags)}")
    
    if tag_display:
        st.write(" | ".join(tag_display[:3]))  # Show first 3 categories
    
    # Display flags if present
    if result['flags']:
        st.warning(f"🚩 **Flags:** {', '.join(result['flags'])}")
    
    return {
        'status': 'success',
        'filename': filename,
        'tags_count': len(result['tags']),
        'flags_count': len(result['flags'])
    }