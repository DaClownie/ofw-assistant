"""
Upload page for document and media file processing
"""
import shutil
import streamlit as st
from pathlib import Path
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


def _render_case_selector():
    """Render case selection/creation dropdown"""
    existing_cases = get_cases()
    case_options = ["-- Select existing case --"] + existing_cases + ["+ Create new case"]
    
    selected_option = st.selectbox("📁 Select or create a case:", case_options)
    
    if selected_option == "-- Select existing case --":
        st.info("👆 Please select an existing case or create a new one")
        return None
    elif selected_option == "+ Create new case":
        case_id = st.text_input("Enter new case ID:")
        if not case_id:
            st.warning("⚠️ Please enter a case ID for the new case")
            return None
        return case_id
    else:
        st.success(f"📂 Selected case: {selected_option}")
        return selected_option


def _render_file_uploader(case_id):
    """Render file uploader and process uploaded files"""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = st.file_uploader(
        "Upload a document", 
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True
    )
    
    if uploaded_files:
        _process_uploaded_files(uploaded_files, case_id)


def _process_uploaded_files(uploaded_files, case_id):
    """Process each uploaded file"""
    for uploaded_file in uploaded_files:
        upload_path = UPLOADS_DIR / uploaded_file.name
        
        # Save uploaded file
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)
        
        st.success(f"✅ File saved: {uploaded_file.name}")
        
        # Process with unified processor
        try:
            _process_file_with_ai(upload_path, uploaded_file.name, case_id)
        except Exception as e:
            st.error(f"❌ Processing failed for {uploaded_file.name}: {str(e)}")
            # Fallback to basic storage
            update_memory(str(upload_path), [], case_id=case_id, flags=[], transcript=None)


def _process_file_with_ai(upload_path, filename, case_id):
    """Process file using unified processor and display results"""
    from app.utils.unified_processor import FileProcessor
    from app.utils.controlled_smart_tagger import controlled_smart_tagger
    
    processor = FileProcessor()
    
    with st.spinner(f"🔄 Processing {filename}..."):
        result = processor.process_file(str(upload_path), case_id)
    
    st.info(f"✅ Processing complete for {filename}!")
    
    # Display tags by category
    categorized = controlled_smart_tagger.get_tag_categories(result['tags'])
    
    for category, tags in categorized.items():
        if tags:
            st.write(f"**{category.replace('_', ' ').title()}:** {', '.join(tags)}")
    
    # Display flags if present
    if result['flags']:
        st.warning(f"🚩 **Flags detected:** {', '.join(result['flags'])}")
    
    # Display transcript/text preview
    if result.get('transcript'):
        st.write("📝 **Transcript/Text preview:**")
        preview = result['transcript'][:500]
        preview_text = preview + ("..." if len(result['transcript']) > 500 else "")
        st.text_area(
            "Preview", 
            value=preview_text, 
            height=150, 
            key=f"preview_{filename}"
        )