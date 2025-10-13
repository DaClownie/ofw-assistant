"""
Memo Builder page for generating and managing case memos
"""
import os
import re
import streamlit as st
from pathlib import Path
from datetime import datetime
from app.utils.memo import (
    get_chunks_by_file, summarize_chunks, save_memo, 
    export_memo_docx, load_memos
)
from app.utils.controlled_smart_tagger import controlled_smart_tagger
from app.utils.model_gpt4 import generate_memo_with_gpt4


def render_memo_builder_page(memory):
    """Render the memo builder page UI"""
    st.header("📝 Memo Builder")
    
    # File selection section
    selection_result = _render_file_selection(memory)
    selected_files = selection_result.get('files', [])
    selection_metadata = selection_result.get('metadata', {})
    
    if selected_files:
        _render_selected_files_summary(selected_files, memory)
        _render_memo_generation(selected_files, memory, selection_metadata)
        _render_memo_content_display()
    
    # Display saved memos
    _render_saved_memos()


def _render_tag_selection(memory):
    """Render tag-based file selection interface"""
    from app.utils.controlled_taxonomy import controlled_taxonomy
    
    # Build tag index: which files have which tags
    tag_index = {}
    all_tags = set()
    
    for fname, meta in memory.items():
        for tag in meta.get('tags', []):
            all_tags.add(tag)
            if tag not in tag_index:
                tag_index[tag] = []
            tag_index[tag].append(fname)
    
    if not all_tags:
        st.warning("No tags found in any files. Upload and process files first.")
        return {'files': [], 'metadata': {}}
    
    # Organize tags by category for better UX
    tags_by_category = {}
    for tag in sorted(all_tags):
        category = controlled_taxonomy.get_category_for_tag(tag)
        if category not in tags_by_category:
            tags_by_category[category] = []
        tags_by_category[category].append(tag)
    
    # Let user choose selection mode
    tag_selection_mode = st.radio(
        "Tag selection mode:",
        ["Select by Category", "Select Individual Tags"],
        help="Category mode selects all files in chosen categories. Individual mode lets you pick specific tags."
    )
    
    selected_files = set()
    selection_metadata = {'tag_selection_mode': tag_selection_mode.lower().replace(' ', '_')}
    
    if tag_selection_mode == "Select by Category":
        # Show categories with file counts
        category_options = []
        for category, tags in sorted(tags_by_category.items()):
            # Count unique files in this category
            category_files = set()
            for tag in tags:
                category_files.update(tag_index.get(tag, []))
            category_options.append(f"{category.replace('_', ' ').title()} ({len(category_files)} files)")
        
        selected_category_labels = st.multiselect(
            "Select categories:",
            category_options,
            help="Select one or more categories to include all files with tags in those categories"
        )
        
        # Extract category names from labels
        selected_categories = [label.split(' (')[0] for label in selected_category_labels]
        selection_metadata['selected_categories'] = selected_categories
        
        # Get all files from selected categories
        for category_display in selected_categories:
            category_key = category_display.lower().replace(' ', '_')
            if category_key in tags_by_category:
                for tag in tags_by_category[category_key]:
                    selected_files.update(tag_index.get(tag, []))
        
        if selected_files:
            st.info(f"📊 Selected {len(selected_files)} files from {len(selected_categories)} categor{'y' if len(selected_categories) == 1 else 'ies'}")
            
            # Show which tags are included
            with st.expander("🏷️ View included tags"):
                for category_display in selected_categories:
                    category_key = category_display.lower().replace(' ', '_')
                    if category_key in tags_by_category:
                        st.markdown(f"**{category_display}:**")
                        tags = tags_by_category[category_key]
                        for tag in tags:
                            file_count = len(tag_index.get(tag, []))
                            st.markdown(f"  - {tag.replace('_', ' ')} ({file_count} files)")
    
    else:  # Individual Tags
        # Create searchable tag list with file counts
        tag_options = []
        for tag in sorted(all_tags):
            category = controlled_taxonomy.get_category_for_tag(tag)
            file_count = len(tag_index.get(tag, []))
            tag_options.append(f"{tag.replace('_', ' ')} ({file_count} files) - {category.replace('_', ' ')}")
        
        selected_tag_labels = st.multiselect(
            "Select tags:",
            tag_options,
            help="Select one or more tags. Files matching ANY selected tag will be included."
        )
        
        # Extract tag names from labels
        selected_tags = [label.split(' (')[0].replace(' ', '_') for label in selected_tag_labels]
        selection_metadata['selected_tags'] = selected_tags
        
        # Get all files with any of the selected tags
        for tag in selected_tags:
            selected_files.update(tag_index.get(tag, []))
        
        if selected_files:
            st.info(f"📊 Selected {len(selected_files)} files matching {len(selected_tags)} tag(s)")
    
    # Show file preview grouped by case
    if selected_files:
        with st.expander("📋 Preview selected files"):
            files_by_case = {}
            for fname in selected_files:
                meta = memory.get(fname, {})
                case_id = meta.get('case_id', 'Unassigned')
                if case_id not in files_by_case:
                    files_by_case[case_id] = []
                files_by_case[case_id].append(fname)
            
            for case_id, files in sorted(files_by_case.items()):
                st.markdown(f"**📁 Case: {case_id}** ({len(files)} files)")
                for fname in sorted(files)[:5]:  # Show first 5 per case
                    st.markdown(f"  - {fname}")
                if len(files) > 5:
                    st.markdown(f"  - ... and {len(files) - 5} more")
    
    return {
        'files': list(selected_files),
        'metadata': selection_metadata
    }


def _render_file_selection(memory):
    """Render file selection interface"""
    st.subheader("📂 Select Files for Memo")
    
    # Organize files by case
    case_files = {}
    for fname, meta in memory.items():
        case_id = meta.get('case_id', 'Unassigned')
        if case_id not in case_files:
            case_files[case_id] = []
        case_files[case_id].append(fname)
    
    # Selection method
    selection_method = st.radio(
        "Selection method:", 
        ["Select by Case", "Select by Tags", "Select Individual Files"]
    )
    
    selected_files = []
    selection_metadata = {'method': selection_method.lower().replace(' ', '_')}
    
    if selection_method == "Select by Case":
        selected_cases = st.multiselect("Select cases to include:", list(case_files.keys()))
        for case in selected_cases:
            selected_files.extend(case_files[case])
        
        if selected_files:
            st.info(f"Selected {len(selected_files)} files from {len(selected_cases)} case(s)")
            selection_metadata['cases'] = selected_cases
    
    elif selection_method == "Select by Tags":
        tag_result = _render_tag_selection(memory)
        selected_files = tag_result.get('files', [])
        selection_metadata.update(tag_result.get('metadata', {}))
    
    else:
        selected_files = st.multiselect("Select individual files:", list(memory.keys()))
    
    return {
        'files': selected_files,
        'metadata': selection_metadata
    }


def _render_selected_files_summary(selected_files, memory):
    """Display summary of selected files"""
    with st.expander("📋 Selected Files Summary"):
        for fname in selected_files:
            meta = memory.get(fname, {})
            case_id = meta.get('case_id', 'Unassigned')
            tags = meta.get('tags', [])
            flags = meta.get('flags', [])
            
            file_info = f"**{fname}** (Case: {case_id})"
            if tags:
                file_info += f" | Tags: {', '.join(tags[:3])}"
                if len(tags) > 3:
                    file_info += f" +{len(tags)-3} more"
            if flags:
                file_info += f" | 🚩 {', '.join(flags)}"
            
            st.markdown(file_info)


def _render_memo_generation(selected_files, memory, selection_metadata):
    """Render memo generation controls"""
    if st.button("🔄 Generate Memo Content"):
        with st.spinner("Processing selected files..."):
            memo_data = _generate_memo_content(selected_files, memory)
            
            if memo_data:
                # Add selection metadata to memo data
                memo_data['selection_metadata'] = selection_metadata
                st.session_state["memo_content"] = memo_data
                st.success("✅ Memo content generated!")


def _generate_memo_content(selected_files, memory):
    """Generate memo content from selected files"""
    summaries = []
    all_tags = set()
    all_flags = set()
    
    for fname in selected_files:
        file_meta = memory.get(fname, {})
        file_path = file_meta.get("path")
        
        if not file_path:
            st.warning(f"⚠️ Skipping: No path found for {fname}")
            continue
        
        try:
            chunks = get_chunks_by_file(file_path)
            summary = summarize_chunks(chunks)
            summaries.append(f"### {fname}\n{summary}")
            
            all_tags.update(file_meta.get('tags', []))
            all_flags.update(file_meta.get('flags', []))
        except Exception as e:
            st.warning(f"⚠️ Failed to process {fname}: {e}")
    
    if summaries:
        return {
            'summary': "\n\n".join(summaries),
            'files': selected_files,
            'tags': list(all_tags),
            'flags': list(all_flags)
        }
    
    return None


def _render_memo_content_display():
    """Display and edit generated memo content"""
    if "memo_content" not in st.session_state:
        return
    
    memo_data = st.session_state["memo_content"]
    
    st.subheader("📄 Generated Memo Content")
    
    # Display tags and flags
    _render_memo_metadata(memo_data)
    
    # Editable memo content
    edited_summary = st.text_area(
        "Memo Content", 
        value=memo_data['summary'], 
        height=400,
        label_visibility="visible",
        help="Edit the memo content as needed before saving or enhancing with AI"
    )
    
    if edited_summary != memo_data['summary']:
        st.session_state["memo_content"]['summary'] = edited_summary
    
    # Save and AI enhancement options
    _render_memo_actions(memo_data)
    
    # Export options
    _render_export_options(memo_data)


def _render_memo_metadata(memo_data):
    """Display tags and flags summary"""
    col1, col2 = st.columns(2)
    
    with col1:
        if memo_data['tags']:
            st.markdown("**🏷️ Tags Found:**")
            categorized = controlled_smart_tagger.get_tag_categories(memo_data['tags'])
            for category, tags in categorized.items():
                if tags:
                    st.markdown(f"- **{category.replace('_', ' ').title()}:** {', '.join(tags)}")
    
    with col2:
        if memo_data['flags']:
            st.markdown("**🚩 Flags Detected:**")
            for flag in memo_data['flags']:
                st.markdown(f"- {flag.replace('_', ' ').title()}")


def _render_memo_actions(memo_data):
    """Render save and AI enhancement controls"""
    st.subheader("💾 Save & Export Options")
    
    # Case ID detection
    case_id = _detect_case_id(memo_data)
    
    # Memo naming
    memo_name = ""
    if case_id:
        memo_name = st.text_input(
            "Memo name/title:", 
            placeholder="e.g., 'Initial Assessment', 'Court Filing Summary'"
        )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧠 Enhance with AI Analysis"):
            _generate_ai_enhanced_memo(memo_data, case_id)
    
    with col2:
        # Save basic memo button - always available
        if st.button("💾 Save Basic Memo"):
            _save_basic_memo_to_case(memo_data, case_id, memo_name)
    
    # Display AI-enhanced memo if generated
    _render_enhanced_memo(case_id, memo_name, memo_data)


def _detect_case_id(memo_data):
    """Auto-detect case ID from selected files"""
    from app.utils.memory import load_memory
    memory = load_memory()
    
    file_cases = set()
    for fname in memo_data['files']:
        file_meta = memory.get(fname, {})
        if file_meta.get('case_id'):
            file_cases.add(file_meta['case_id'])
    
    if len(file_cases) == 1:
        default_case = list(file_cases)[0]
        st.info(f"📂 All selected files are from case: **{default_case}**")
        return st.text_input("Case ID for this memo:", value=default_case)
    elif len(file_cases) > 1:
        st.warning(f"⚠️ Selected files are from multiple cases: {', '.join(file_cases)}")
        return st.selectbox("Choose case for this memo:", [''] + list(file_cases))
    else:
        st.info("📂 Selected files have no case assigned")
        return st.text_input("Case ID for this memo:")


def _generate_ai_enhanced_memo(memo_data, case_id):
    """Generate AI-enhanced professional memo"""
    with st.spinner("Generating professional memo with AI..."):
        try:
            edited_summary = st.session_state["memo_content"]['summary']
            analysis = controlled_smart_tagger.analyze_text_comprehensive(edited_summary)
            
            prompt = _build_memo_prompt(memo_data, case_id, analysis, edited_summary)
            ai_generated_memo = generate_memo_with_gpt4(prompt)
            
            # Store both display and export versions
            st.session_state["enhanced_memo_display"] = _format_display_memo(
                ai_generated_memo, case_id, memo_data, analysis
            )
            st.session_state["enhanced_memo_export"] = _format_export_memo(
                ai_generated_memo, case_id, memo_data, analysis
            )
        except Exception as e:
            st.error(f"Failed to generate AI memo: {str(e)}")


def _build_memo_prompt(memo_data, case_id, analysis, summary):
    """Build comprehensive prompt for GPT-4 memo generation"""
    
    # Determine selection context from metadata
    selection_context = ""
    metadata = memo_data.get('selection_metadata', {})
    method = metadata.get('method', '')
    
    if method == 'select_by_tags':
        tag_mode = metadata.get('tag_selection_mode', '')
        if tag_mode == 'select_by_category':
            categories = metadata.get('selected_categories', [])
            if categories:
                selection_context = f"\n\nFILE SELECTION CRITERIA: Documents were specifically filtered to include files tagged in these categories: {', '.join(categories)}. This memo focuses exclusively on these topical areas."
        elif tag_mode == 'select_individual_tags':
            tags = metadata.get('selected_tags', [])
            if tags:
                formatted_tags = [tag.replace('_', ' ').title() for tag in tags]
                selection_context = f"\n\nFILE SELECTION CRITERIA: Documents were specifically filtered to include files with these tags: {', '.join(formatted_tags)}. This memo focuses exclusively on these specific concerns."
    
    return f"""You are a legal case analyst. Write a professional memo for case {case_id or 'General'}.{selection_context}

SOURCE DOCUMENTS ({len(memo_data['files'])} files):
{chr(10).join(f'- {f}' for f in memo_data['files'])}

IDENTIFIED CONCERNS:
{chr(10).join(f'- {tag.replace("_", " ").title()}' for tag in analysis['tags'])}

PRIORITY FLAGS:
{chr(10).join(f'- {tag.replace("_", " ").title()}' for tag in analysis['priority_tags']) if analysis['priority_tags'] else '- None'}

Safety Assessment: {'CONCERNS PRESENT' if analysis['has_safety_concerns'] else 'No immediate safety issues'}
Fabrication Indicators: {'PRESENT - Recommend investigation' if analysis['has_fabricated_concerns'] else 'Not detected'}

CONTENT SUMMARY:
{summary[:1500]}

Write a concise 3-paragraph professional memo:
1. Overview of documents reviewed and timeline
2. Key findings and concerning patterns with specific examples
3. Recommended actions or areas requiring attention

Use professional legal memo tone. Be specific and factual."""


def _format_display_memo(ai_memo, case_id, memo_data, analysis):
    """Format memo for markdown display"""
    categories_text = ', '.join(analysis['categories'].keys()) if analysis['categories'] else 'None'
    
    return f"""# Case Memo: {case_id or 'General'}

{ai_memo}

---

### Analysis Summary
**Files Reviewed:** {len(memo_data['files'])}  
**Categories Identified:** {categories_text}  
**Priority Concerns:** {len(analysis['priority_tags'])}  
**Safety Issues:** {'Yes' if analysis['has_safety_concerns'] else 'No'}  
**Fabrication Indicators:** {'Yes' if analysis['has_fabricated_concerns'] else 'No'}
"""


def _format_export_memo(ai_memo, case_id, memo_data, analysis):
    """Format memo for plain text export"""
    categories_text = ', '.join(analysis['categories'].keys()) if analysis['categories'] else 'None'
    
    return f"""CASE MEMO: {case_id or 'General'}

{ai_memo}

---
ANALYSIS SUMMARY
Files Reviewed: {len(memo_data['files'])}
Categories: {categories_text}
Priority Concerns: {len(analysis['priority_tags'])}
Safety Issues: {'Yes' if analysis['has_safety_concerns'] else 'No'}
Fabrication Indicators: {'Yes' if analysis['has_fabricated_concerns'] else 'No'}
"""


def _save_basic_memo_to_case(memo_data, case_id, memo_name):
    """Save basic (non-AI) memo to case"""
    if not case_id:
        st.warning("⚠️ Please enter a case ID to save")
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    full_memo_name = f"{memo_name} - Basic ({timestamp})" if memo_name else f"Memo - Basic ({timestamp})"
    
    # Always save the basic edited summary
    edited_summary = st.session_state["memo_content"]['summary']
    
    memo_metadata = f"\n\n---\nGenerated: {timestamp}\nFiles included: {len(memo_data['files'])}\nType: Basic"
    memo_with_metadata = edited_summary + memo_metadata
    
    save_memo(case_id.strip(), memo_with_metadata, sources=memo_data['files'], memo_name=full_memo_name)
    st.success(f"✅ Basic memo '{full_memo_name}' saved to case: {case_id.strip()}")


def _save_ai_memo_to_case(memo_data, case_id, memo_name):
    """Save AI-enhanced memo to case"""
    if not case_id:
        st.warning("⚠️ Please enter a case ID to save")
        return
    
    if "enhanced_memo_export" not in st.session_state:
        st.warning("⚠️ No AI-enhanced memo to save. Generate one first!")
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    full_memo_name = f"{memo_name} - AI Enhanced ({timestamp})" if memo_name else f"Memo - AI Enhanced ({timestamp})"
    
    # Save the AI-enhanced version
    memo_to_save = st.session_state["enhanced_memo_export"]
    
    memo_metadata = f"\n\n---\nGenerated: {timestamp}\nFiles included: {len(memo_data['files'])}\nType: AI-Enhanced"
    memo_with_metadata = memo_to_save + memo_metadata
    
    save_memo(case_id.strip(), memo_with_metadata, sources=memo_data['files'], memo_name=full_memo_name)
    st.success(f"✅ AI-enhanced memo '{full_memo_name}' saved to case: {case_id.strip()}")


def _render_enhanced_memo(case_id, memo_name, memo_data):
    """Display AI-enhanced memo if it exists"""
    if "enhanced_memo_display" not in st.session_state:
        return
    
    st.subheader("🧠 AI-Enhanced Memo")
    st.markdown(st.session_state["enhanced_memo_display"])
    
    # Save AI-enhanced memo button
    if st.button("💾 Save AI-Enhanced Memo"):
        _save_ai_memo_to_case(memo_data, case_id, memo_name)
    
    if st.checkbox("✏️ Edit enhanced memo"):
        edited_enhanced = st.text_area(
            "Enhanced Memo Content", 
            value=st.session_state["enhanced_memo_display"], 
            height=300,
            label_visibility="visible"
        )
        
        if edited_enhanced != st.session_state["enhanced_memo_display"]:
            st.session_state["enhanced_memo_display"] = edited_enhanced
            # Convert to export format
            export_version = re.sub(r'#+\s*', '', edited_enhanced)
            export_version = re.sub(r'\*\*(.*?)\*\*', r'\1', export_version)
            st.session_state["enhanced_memo_export"] = export_version


def _render_export_options(memo_data):
    """Render export buttons"""
    st.subheader("📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as .txt"):
            _export_as_txt(memo_data)
    
    with col2:
        if st.button("📄 Export as .docx"):
            _export_as_docx(memo_data)
    
    with col3:
        if st.button("🗑️ Clear Memo"):
            _clear_memo()


def _export_as_txt(memo_data):
    """Export memo as text file"""
    from app.utils.memory import load_memory
    memory = load_memory()
    
    # Get case ID and memo name
    file_cases = set()
    for fname in memo_data['files']:
        file_meta = memory.get(fname, {})
        if file_meta.get('case_id'):
            file_cases.add(file_meta['case_id'])
    
    case_id = list(file_cases)[0] if len(file_cases) == 1 else 'nocase'
    
    edited_summary = st.session_state["memo_content"]['summary']
    content = st.session_state.get("enhanced_memo_export", edited_summary)
    
    filename = f"memo_export_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(filename, "w") as f:
        f.write(content)
    st.success(f"Exported as {filename}")


def _export_as_docx(memo_data):
    """Export memo as Word document"""
    from app.utils.memory import load_memory
    memory = load_memory()
    
    file_cases = set()
    for fname in memo_data['files']:
        file_meta = memory.get(fname, {})
        if file_meta.get('case_id'):
            file_cases.add(file_meta['case_id'])
    
    case_id = list(file_cases)[0] if len(file_cases) == 1 else 'General'
    
    filename = f"memo_export_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    downloads_folder = Path(os.path.expanduser("~/Downloads/ofw"))
    downloads_folder.mkdir(parents=True, exist_ok=True)
    output_path = downloads_folder / filename
    
    edited_summary = st.session_state["memo_content"]['summary']
    content = st.session_state.get("enhanced_memo_export", edited_summary)
    
    export_memo_docx(case_id, content, output_path)
    st.success(f"Exported to {output_path}")


def _clear_memo():
    """Clear memo from session state"""
    keys_to_remove = ["memo_content", "enhanced_memo_display", "enhanced_memo_export"]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def _render_saved_memos():
    """Display all saved memos"""
    st.subheader("📂 Saved Memos")
    saved_memos = load_memos()
    
    if not saved_memos:
        st.info("No saved memos yet. Create one above!")
        return
    
    for cid, memo_data in saved_memos.items():
        # Handle both old and new format
        memo_list = memo_data if isinstance(memo_data, list) else [memo_data]
        
        with st.expander(f"📋 Case: {cid} ({len(memo_list)} memo(s))"):
            for i, memo_obj in enumerate(memo_list):
                _render_saved_memo(memo_obj, cid, i)


def _render_saved_memo(memo_obj, case_id, index):
    """Render a single saved memo"""
    memo_name = memo_obj.get("memo_name", f"Memo {index+1}")
    memo_text = memo_obj.get("memo_text", "")
    sources = memo_obj.get("sources", [])
    
    st.markdown(f"**{memo_name}**")
    preview = memo_text[:300] + ("..." if len(memo_text) > 300 else "")
    st.text_area("Memo Preview", value=preview, height=100, disabled=True, 
                 key=f"preview_{case_id}_{index}", label_visibility="collapsed")
    
    if sources:
        sources_preview = ', '.join(sources[:3]) + ('...' if len(sources) > 3 else '')
        st.markdown(f"*Sources: {sources_preview}*")
    
    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export as .txt", key=f"{case_id}_{index}_txt"):
            _export_saved_memo_txt(memo_name, case_id, memo_text)
    
    with col2:
        if st.button("Export as .docx", key=f"{case_id}_{index}_docx"):
            _export_saved_memo_docx(memo_name, case_id, memo_text)
    
    if index < len(memo_obj) - 1:
        st.markdown("---")


def _export_saved_memo_txt(memo_name, case_id, memo_text):
    """Export saved memo as text"""
    safe_name = memo_name.replace(' ', '_')
    filename = f"{safe_name}_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w") as f:
        f.write(memo_text)
    st.success(f"Exported as {filename}")


def _export_saved_memo_docx(memo_name, case_id, memo_text):
    """Export saved memo as Word document"""
    safe_name = memo_name.replace(' ', '_')
    filename = f"{safe_name}_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    downloads_folder = Path(os.path.expanduser("~/Downloads/ofw"))
    downloads_folder.mkdir(parents=True, exist_ok=True)
    output_path = downloads_folder / filename
    export_memo_docx(case_id, memo_text, output_path)
    st.success(f"Exported to {output_path}")