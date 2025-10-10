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
    selected_files = _render_file_selection(memory)
    
    if selected_files:
        _render_selected_files_summary(selected_files, memory)
        _render_memo_generation(selected_files, memory)
        _render_memo_content_display()
    
    # Display saved memos
    _render_saved_memos()


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
        ["Select by Case", "Select Individual Files"]
    )
    
    selected_files = []
    
    if selection_method == "Select by Case":
        selected_cases = st.multiselect("Select cases to include:", list(case_files.keys()))
        for case in selected_cases:
            selected_files.extend(case_files[case])
        
        if selected_files:
            st.info(f"Selected {len(selected_files)} files from {len(selected_cases)} case(s)")
    else:
        selected_files = st.multiselect("Select individual files:", list(memory.keys()))
    
    return selected_files


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


def _render_memo_generation(selected_files, memory):
    """Render memo generation controls"""
    if st.button("🔄 Generate Memo Content"):
        with st.spinner("Processing selected files..."):
            memo_data = _generate_memo_content(selected_files, memory)
            
            if memo_data:
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
        "✏️ Memo Content (editable):", 
        value=memo_data['summary'], 
        height=400
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
        if st.button("💾 Save Memo to Case"):
            _save_memo_to_case(memo_data, case_id, memo_name)
    
    # Display AI-enhanced memo if generated
    _render_enhanced_memo()


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
    return f"""You are a legal case analyst. Write a professional memo for case {case_id or 'General'}.

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


def _save_memo_to_case(memo_data, case_id, memo_name):
    """Save memo to case"""
    if not case_id:
        st.warning("⚠️ Please enter a case ID to save")
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    full_memo_name = f"{memo_name} ({timestamp})" if memo_name else f"Memo - {timestamp}"
    
    # Use AI-enhanced version if available
    edited_summary = st.session_state["memo_content"]['summary']
    memo_to_save = st.session_state.get("enhanced_memo_export", edited_summary)
    
    memo_metadata = f"\n\n---\nGenerated: {timestamp}\nFiles included: {len(memo_data['files'])}\nType: {'AI-Enhanced' if 'enhanced_memo_export' in st.session_state else 'Basic'}"
    memo_with_metadata = memo_to_save + memo_metadata
    
    save_memo(case_id.strip(), memo_with_metadata, sources=memo_data['files'], memo_name=full_memo_name)
    st.success(f"✅ Memo '{full_memo_name}' saved to case: {case_id.strip()}")


def _render_enhanced_memo():
    """Display AI-enhanced memo if it exists"""
    if "enhanced_memo_display" not in st.session_state:
        return
    
    st.subheader("🧠 AI-Enhanced Memo")
    st.markdown(st.session_state["enhanced_memo_display"])
    
    if st.checkbox("✏️ Edit enhanced memo"):
        edited_enhanced = st.text_area(
            "Edit enhanced memo:", 
            value=st.session_state["enhanced_memo_display"], 
            height=300
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
    st.text_area("", value=preview, height=100, disabled=True, key=f"preview_{case_id}_{index}")
    
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