import os
import shutil
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from app.utils.parser import load_and_split_pdf
from app.utils.tagging import hybrid_tag
from app.utils.model_gpt4 import tag_with_gpt4
from app.utils.model_llama import tag_with_llama
from app.utils.memory import update_memory
from app.utils.memory import load_memory
from app.utils.vectorstore import persist_chunks
from app.utils.memo import load_memos

# warning/error handling
os.environ["TOKENIZERS_PARALLELISM"] = "false"
try:
    import torch
    torch._classes = {}  # disable dynamic class lookup error
except:
    pass

# Load or request OpenAI API key
ENV_PATH = Path(".env")

def ensure_api_key():
    if not ENV_PATH.exists():
        with st.form("api_key_form"):
            st.write("🔑 Enter your OpenAI API Key")
            api_key_input = st.text_input("API Key", type="password")
            submitted = st.form_submit_button("Save")
            if submitted:
                ENV_PATH.write_text(f"OPENAI_API_KEY={api_key_input.strip()}")
                st.success("API key saved. Please reload.")
                st.stop()
    else:
        load_dotenv(dotenv_path=ENV_PATH)

# Initialize Streamlit UI
KEY_PHRASES = ["court order", "emotional harm", "diagnosis", "manipulation", "parenting time"]
TOKEN_LIMIT = 1000  # adjustable

def should_use_gpt4(text):
    if any(phrase in text.lower() for phrase in KEY_PHRASES):
        return True
    if len(text.split()) > TOKEN_LIMIT:
        return True
    return False

def main():
    st.set_page_config(page_title="OFW Assistant", layout="centered")
    st.title("📄 OFW Assistant")

    # Scrollbar fix
    st.markdown("""
    <style>
    ::-webkit-scrollbar {
        width: 12px;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #bbb;
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #888;
    }
    </style>
    """, unsafe_allow_html=True)

    ensure_api_key()
    st.sidebar.title("OFW Assistant")
    page = st.sidebar.radio("Navigation", ["Upload", "Dashboard", "Memo Builder"])

    # Project Settings in sidebar
    st.sidebar.markdown("---")
    from app.utils.project_settings import load_project_settings, save_project_settings
    with st.sidebar.expander("⚙️ AI Instructions"):
        settings = load_project_settings()
        
        instructions = st.text_area(
            "AI Analysis Instructions:",
            value=settings.get("instructions", ""),
            height=300,
            help="These instructions guide all AI analysis and memo generation"
        )
        
        if st.button("Save Instructions"):
            save_project_settings({
                "instructions": instructions
            })
            st.success("Instructions saved!")

    with st.sidebar.expander("📁 Local Storage"):
        if st.button("📁 Open File Storage"):
            import platform
            import subprocess
            import time
            
            # Create user-friendly storage location
            storage_path = Path.home() / "OFW_Assistant_Files"
            storage_path.mkdir(exist_ok=True)
            
            # Copy case files to user directory if they don't exist
            source_path = Path("data/case_files")
            if source_path.exists():
                
                for case_folder in source_path.iterdir():
                    if case_folder.is_dir():
                        dest_folder = storage_path / case_folder.name
                        if not dest_folder.exists():
                            shutil.copytree(case_folder, dest_folder)
            
            # Open the folder in file explorer
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(storage_path)])
                elif platform.system() == "Windows":
                    subprocess.run(["explorer", str(storage_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(storage_path)])
                success_placeholder = st.sidebar.empty()
                success_placeholder.success("File storage opened!")

                time.sleep(2)  # Show for 2 seconds
                success_placeholder.empty()  # Clear the message
            except Exception as e:
                st.error(f"Could not open folder: {e}")
                st.code(f"Files are stored at: {storage_path}")
        # Warning note about file deletion
        st.caption("⚠️ Note: Deleting local files will break memo generation functionality")

    # API Key Management
    with st.sidebar.expander("🔑 API Key Management"):
        # Current API key status
        if ENV_PATH.exists():
            # Show masked current key
            try:
                with open(ENV_PATH, 'r') as f:
                    current_key_line = f.read().strip()
                    if "OPENAI_API_KEY=" in current_key_line:
                        current_key = current_key_line.split("=", 1)[1]
                        masked_key = f"{current_key[:8]}{'*' * 20}{current_key[-4:]}" if len(current_key) > 12 else "***"
                        st.text_input("Current Key:", value=masked_key, disabled=True)
            except:
                st.text_input("Current Key:", value="[Error reading key]", disabled=True)
        else:
            st.text_input("Current Key:", value="No key set", disabled=True)

        # Update API key
        st.markdown("**⚠️ Update API Key**")
        # Link to OpenAI API page
        st.markdown("[Get OpenAI API Key](https://platform.openai.com/api-keys)")
        new_api_key = st.text_input("New API Key:", type="password", help="Enter your OpenAI API key")
            
        if st.button("Update Key"):
            if new_api_key.strip():
                try:
                    ENV_PATH.write_text(f"OPENAI_API_KEY={new_api_key.strip()}")
                    st.success("API key updated! Please refresh the page.")
                    # Force reload of environment
                    load_dotenv(dotenv_path=ENV_PATH, override=True)
                except Exception as e:
                    st.error(f"Failed to update API key: {e}")
            else:
                st.warning("Please enter a valid API key")

    memory = load_memory()
    if page == "Upload":
        st.header("📤 Upload Documents or Audio")
        
        from app.utils.memory import get_cases

        # Get existing cases
        existing_cases = get_cases()
        case_options = ["-- Select existing case --"] + existing_cases + ["+ Create new case"]

        selected_option = st.selectbox("📝 Select or create a case:", case_options)

        case_id = ""
        if selected_option == "-- Select existing case --":
            st.info("👆 Please select an existing case or create a new one")
        elif selected_option == "+ Create new case":
            case_id = st.text_input("Enter new case ID:")
            if not case_id:
                st.warning("⚠️ Please enter a case ID for the new case")
        else:
            case_id = selected_option
            st.success(f"📁 Selected case: {case_id}")

        if not case_id:
            st.warning("⚠️ Please select or create a case before uploading.")
        else:
            Path("data/uploads").mkdir(parents=True, exist_ok=True)
            uploaded_files = st.file_uploader(
                "Upload a document", 
                type=["pdf", "docx", "txt", "eml", "mp3", "m4a", "jpg", "jpeg", "png", "heic", "tiff", "gif", "bmp", "mp4", "mov", "mkv", "avi"],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    upload_path = Path("data/uploads") / uploaded_file.name
                    
                    # Save uploaded file
                    with open(upload_path, "wb") as f:
                        shutil.copyfileobj(uploaded_file, f)
                    
                    st.success(f"✅ File saved: {uploaded_file.name}")
                    
                    # Process with unified processor
                    try:
                        from app.utils.unified_processor import FileProcessor
                        processor = FileProcessor()
                        
                        with st.spinner(f"🔄 Processing {uploaded_file.name}..."):
                            result = processor.process_file(str(upload_path), case_id)
                        
                        # Display results for this file
                        st.info(f"✅ Processing complete for {uploaded_file.name}!")
                        
                        # Show tags by category
                        from app.utils.controlled_smart_tagger import controlled_smart_tagger
                        categorized = controlled_smart_tagger.get_tag_categories(result['tags'])
                        
                        for category, tags in categorized.items():
                            if tags:
                                st.write(f"**{category.replace('_', ' ').title()}:** {', '.join(tags)}")
                        
                        if result['flags']:
                            st.warning(f"🚩 **Flags detected:** {', '.join(result['flags'])}")
                        
                        if result.get('transcript'):
                            st.write("📝 **Transcript/Text preview:**")
                            preview = result['transcript'][:500]
                            st.text_area("Preview", value=preview + ("..." if len(result['transcript']) > 500 else ""), height=150, key=f"preview_{uploaded_file.name}")
                            
                    except Exception as e:
                        st.error(f"❌ Processing failed for {uploaded_file.name}: {str(e)}")
                        # Fallback to basic storage
                        from app.utils.memory import update_memory
                        update_memory(str(upload_path), [], case_id=case_id, flags=[], transcript=None)

    elif page == "Dashboard":
        st.header("📊 Dashboard")
        from app.utils.memory import get_cases

        # Load memory and taxonomy
        from app.utils.controlled_taxonomy import controlled_taxonomy
        from app.utils.controlled_smart_tagger import controlled_smart_tagger

        # 📊 Overview Stats
        st.subheader("📊 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        total_files = len(memory)
        total_cases = len(get_cases())
        
        # Count flags and priority tags
        total_flags = sum(len(meta.get("flags", [])) for meta in memory.values())
        safety_files = sum(1 for meta in memory.values() 
                        if any(controlled_taxonomy.get_category_for_tag(tag) == 'safety_concerns' 
                                for tag in meta.get("tags", [])))
        
        col1.metric("Total Files", total_files)
        col2.metric("Active Cases", total_cases)
        col3.metric("Total Flags", total_flags)
        col4.metric("Safety Concerns", safety_files)

        # 🏷️ Filter by Category
        st.subheader("🏷️ Browse by Category")
        
        # Group files by tag categories
        category_data = {}
        for fname, meta in memory.items():
            for tag in meta.get("tags", []):
                category = controlled_taxonomy.get_category_for_tag(tag)
                if category not in category_data:
                    category_data[category] = {}
                if tag not in category_data[category]:
                    category_data[category][tag] = []
                category_data[category][tag].append({
                    'file': fname,
                    'case_id': meta.get('case_id', 'Unassigned'),
                    'flags': meta.get('flags', [])
                })

        # Display categories with priority order
        priority_categories = ['safety_concerns', 'fabricated_concerns', 'legal_process', 'mental_health']
        all_categories = priority_categories + [cat for cat in sorted(category_data.keys()) if cat not in priority_categories]

        for category in all_categories:
            if category in category_data:
                tag_dict = category_data[category]
                total_files_in_category = sum(len(files) for files in tag_dict.values())
                
                # Special styling for high-priority categories
                if category in priority_categories[:2]:  # safety_concerns, fabricated_concerns
                    icon = "🚨" if category == 'safety_concerns' else "⚠️"
                else:
                    icon = "📂"
                
                with st.expander(f"{icon} {category.replace('_', ' ').title()} ({total_files_in_category} files)"):
                    for tag, file_data in sorted(tag_dict.items()):
                        st.markdown(f"**#{tag.replace('_', ' ')}** ({len(file_data)} files)")
                        
                        # Group by case for better organization
                        by_case = {}
                        for item in file_data:
                            case = item['case_id']
                            if case not in by_case:
                                by_case[case] = []
                            by_case[case].append(item)
                        
                        for case, items in sorted(by_case.items()):
                            st.markdown(f"  📁 **Case: {case}**")
                            for item in items[:3]:  # Show first 3 files per case
                                flag_str = f" 🚩 {' / '.join(item['flags'])}" if item['flags'] else ""
                                st.markdown(f"    - {item['file']}{flag_str}")
                            if len(items) > 3:
                                st.markdown(f"    - ... and {len(items) - 3} more files")

        # 📁 Filter by Case
        st.subheader("📁 Browse by Case")
        case_tabs = st.tabs(["All Cases"] + list(get_cases())[:5])  # Show first 5 cases as tabs
        
        with case_tabs[0]:  # All Cases tab
            for cid in get_cases():
                case_files = [(fname, meta) for fname, meta in memory.items() if meta.get("case_id") == cid]
                
                # Count different types of content in this case
                has_transcript = any(meta.get("transcript") for fname, meta in case_files)
                total_flags = sum(len(meta.get("flags", [])) for fname, meta in case_files)
                
                case_info = f"📁 **{cid}** ({len(case_files)} files"
                if has_transcript:
                    case_info += " 🎙️"
                if total_flags > 0:
                    case_info += f" 🚩{total_flags}"
                
                with st.expander(case_info):
                    # Show case summary
                    all_tags = set()
                    for fname, meta in case_files:
                        all_tags.update(meta.get("tags", []))
                    
                    if all_tags:
                        case_categories = {}
                        for tag in all_tags:
                            cat = controlled_taxonomy.get_category_for_tag(tag)
                            case_categories.setdefault(cat, []).append(tag)
                        
                        st.markdown("**Case Profile:**")
                        for cat, tags in case_categories.items():
                            st.markdown(f"- {cat.replace('_', ' ').title()}: {', '.join(tags)}")
                    
                    st.markdown("**Files:**")
                    for fname, meta in case_files:
                        flags = meta.get("flags", [])
                        flag_str = f" 🚩 {' / '.join(flags)}" if flags else ""
                        file_type = "🎙️" if meta.get("transcript") else "📄"
                        st.markdown(f"  {file_type} {fname}{flag_str}")

        # 🔍 Enhanced Search
        st.subheader("🔍 Smart Search")
        search_query = st.text_input("Search files, tags, or content:")
        
        if search_query:
            st.markdown(f"**Results for:** `{search_query}`")
            search_results = []
            
            # Search in different places
            search_lower = search_query.lower()
            
            for fname, meta in memory.items():
                score = 0
                reasons = []
                
                # Search in tags
                matching_tags = [tag for tag in meta.get("tags", []) if search_lower in tag.lower()]
                if matching_tags:
                    score += len(matching_tags) * 3
                    reasons.append(f"Tags: {', '.join(matching_tags)}")
                
                # Search in flags
                matching_flags = [flag for flag in meta.get("flags", []) if search_lower in flag.lower()]
                if matching_flags:
                    score += len(matching_flags) * 2
                    reasons.append(f"Flags: {', '.join(matching_flags)}")
                
                # Search in transcript
                transcript = meta.get("transcript") or ""
                if search_lower in transcript.lower():
                    score += 1
                    reasons.append("Found in transcript")
                
                # Search in filename
                if search_lower in fname.lower():
                    score += 1
                    reasons.append("Found in filename")
                
                if score > 0:
                    search_results.append({
                        'file': fname,
                        'case_id': meta.get('case_id', 'Unassigned'),
                        'score': score,
                        'reasons': reasons,
                        'flags': meta.get('flags', [])
                    })
            
            # Sort by relevance score
            search_results.sort(key=lambda x: x['score'], reverse=True)
            
            if search_results:
                for result in search_results[:10]:  # Show top 10 results
                    flag_str = f" 🚩 {' / '.join(result['flags'])}" if result['flags'] else ""
                    st.markdown(f"**{result['file']}** (Case: {result['case_id']}){flag_str}")
                    st.markdown(f"  - {' | '.join(result['reasons'])}")
            else:
                st.info("No matches found.")

        # 📊 Analytics Charts
        st.subheader("📊 Analytics")
        
        # Flags per case chart
        import pandas as pd
        
        chart_data = []
        for cid in get_cases():
            case_flags = {}
            for fname, meta in memory.items():
                if meta.get("case_id") == cid:
                    for flag in meta.get("flags", []):
                        case_flags[flag] = case_flags.get(flag, 0) + 1
            
            total_flags = sum(case_flags.values())
            chart_data.append({"Case": cid, "Total Flags": total_flags})
        
        if chart_data:
            df = pd.DataFrame(chart_data)
            st.bar_chart(df.set_index("Case"))

        # Vector search (keep your existing functionality)
        st.subheader("🔍 Content Search")
        query = st.text_input("Search stored content:")
        if query:
            from app.utils.vectorstore import search_similar
            results = search_similar(query)
            for doc in results:
                st.markdown(f"**Match:** {doc.page_content[:200]}...")

    elif page == "Memo Builder":
        st.header("📝 Memo Builder")

        # Import required modules
        from app.utils.memo import get_chunks_by_file, summarize_chunks, save_memo, export_memo_docx
        from app.utils.controlled_smart_tagger import controlled_smart_tagger
        from app.utils.controlled_taxonomy import controlled_taxonomy

        # File Selection
        st.subheader("📁 Select Files for Memo")
        
        # Organize files by case for easier selection
        case_files = {}
        for fname, meta in memory.items():
            case_id = meta.get('case_id', 'Unassigned')
            if case_id not in case_files:
                case_files[case_id] = []
            case_files[case_id].append(fname)
        
        # Let user select by case or individual files
        selection_method = st.radio("Selection method:", ["Select by Case", "Select Individual Files"])
        
        selected_files = []
        
        if selection_method == "Select by Case":
            selected_cases = st.multiselect("Select cases to include:", list(case_files.keys()))
            for case in selected_cases:
                selected_files.extend(case_files[case])
            
            if selected_files:
                st.info(f"Selected {len(selected_files)} files from {len(selected_cases)} case(s)")
        else:
            selected_files = st.multiselect("Select individual files:", list(memory.keys()))

        if selected_files:
            # Show file summary
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

            # Process selected files
            if st.button("🔄 Generate Memo Content"):
                with st.spinner("Processing selected files..."):
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
                            
                            # Collect tags and flags
                            all_tags.update(file_meta.get('tags', []))
                            all_flags.update(file_meta.get('flags', []))
                            
                        except Exception as e:
                            st.warning(f"⚠️ Failed to process {fname}: {e}")

                    if summaries:
                        combined_summary = "\n\n".join(summaries)
                        
                        # Store in session state
                        st.session_state["memo_content"] = {
                            'summary': combined_summary,
                            'files': selected_files,
                            'tags': list(all_tags),
                            'flags': list(all_flags)
                        }
                        
                        st.success("✅ Memo content generated!")

            # Display generated content
            if "memo_content" in st.session_state:
                memo_data = st.session_state["memo_content"]
                
                st.subheader("📄 Generated Memo Content")
                
                # Show tags and flags summary
                col1, col2 = st.columns(2)
                with col1:
                    if memo_data['tags']:
                        st.markdown("**🏷️ Tags Found:**")
                        # Group tags by category
                        categorized = controlled_smart_tagger.get_tag_categories(memo_data['tags'])
                        for category, tags in categorized.items():
                            if tags:
                                st.markdown(f"- **{category.replace('_', ' ').title()}:** {', '.join(tags)}")
                
                with col2:
                    if memo_data['flags']:
                        st.markdown("**🚩 Flags Detected:**")
                        for flag in memo_data['flags']:
                            st.markdown(f"- {flag.replace('_', ' ').title()}")

                # Editable memo content
                edited_summary = st.text_area(
                    "📝 Memo Content (editable):", 
                    value=memo_data['summary'], 
                    height=400
                )
                
                # Update session state if content is edited
                if edited_summary != memo_data['summary']:
                    st.session_state["memo_content"]['summary'] = edited_summary

                # Case ID for saving
                st.subheader("💾 Save & Export Options")
                # Auto-detect case ID from selected files
                file_cases = set()
                for fname in memo_data['files']:
                    file_meta = memory.get(fname, {})
                    if file_meta.get('case_id'):
                        file_cases.add(file_meta['case_id'])

                if len(file_cases) == 1:
                    # All files from same case - use that case
                    default_case = list(file_cases)[0]
                    st.info(f"📁 All selected files are from case: **{default_case}**")
                    case_id = st.text_input("Case ID for this memo:", value=default_case)
                elif len(file_cases) > 1:
                    # Files from multiple cases
                    st.warning(f"⚠️ Selected files are from multiple cases: {', '.join(file_cases)}")
                    case_id = st.selectbox("Choose case for this memo:", [''] + list(file_cases))
                else:
                    # No case assigned to files
                    st.info("📝 Selected files have no case assigned")
                    case_id = st.text_input("Case ID for this memo:")

                # Memo naming
                if case_id:
                    memo_name = st.text_input("Memo name/title:", 
                                            placeholder="e.g., 'Initial Assessment', 'Court Filing Summary', 'Safety Concerns Review'")
                else:
                    memo_name = ""

                # Enhanced memo generation with AI
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🧠 Enhance with AI Analysis"):
                        with st.spinner("Generating professional memo with AI..."):
                            try:
                                from app.utils.model_gpt4 import generate_memo_with_gpt4
                                analysis = controlled_smart_tagger.analyze_text_comprehensive(edited_summary)
                                
                                # Build comprehensive prompt for GPT-4
                                prompt = f"""You are a legal case analyst. Write a professional memo for case {case_id or 'General'}.

SOURCE DOCUMENTS ({len(memo_data['files'])} files):
{chr(10).join(f'- {f}' for f in memo_data['files'])}

IDENTIFIED CONCERNS:
{chr(10).join(f'- {tag.replace("_", " ").title()}' for tag in analysis['tags'])}

PRIORITY FLAGS:
{chr(10).join(f'- {tag.replace("_", " ").title()}' for tag in analysis['priority_tags']) if analysis['priority_tags'] else '- None'}

Safety Assessment: {'CONCERNS PRESENT' if analysis['has_safety_concerns'] else 'No immediate safety issues'}
Fabrication Indicators: {'PRESENT - Recommend investigation' if analysis['has_fabricated_concerns'] else 'Not detected'}

CONTENT SUMMARY:
{edited_summary[:1500]}

Write a concise 3-paragraph professional memo:
1. Overview of documents reviewed and timeline
2. Key findings and concerning patterns with specific examples
3. Recommended actions or areas requiring attention

Use professional legal memo tone. Be specific and factual."""

                                # Generate actual AI memo
                                ai_generated_memo = generate_memo_with_gpt4(prompt)
                                
                                # Build category list
                                categories_text = ', '.join(analysis['categories'].keys()) if analysis['categories'] else 'None'
                                
                                # Format for display with markdown
                                display_memo = f"""# Case Memo: {case_id or 'General'}

{ai_generated_memo}

---

### Analysis Summary
**Files Reviewed:** {len(memo_data['files'])}  
**Categories Identified:** {categories_text}  
**Priority Concerns:** {len(analysis['priority_tags'])}  
**Safety Issues:** {'Yes' if analysis['has_safety_concerns'] else 'No'}  
**Fabrication Indicators:** {'Yes' if analysis['has_fabricated_concerns'] else 'No'}
"""
                
                # Plain text for export (no markdown)
                                export_memo = f"""CASE MEMO: {case_id or 'General'}

{ai_generated_memo}

---
ANALYSIS SUMMARY
Files Reviewed: {len(memo_data['files'])}
Categories: {categories_text}
Priority Concerns: {len(analysis['priority_tags'])}
Safety Issues: {'Yes' if analysis['has_safety_concerns'] else 'No'}
Fabrication Indicators: {'Yes' if analysis['has_fabricated_concerns'] else 'No'}
"""
                
                                st.session_state["enhanced_memo_display"] = display_memo
                                st.session_state["enhanced_memo_export"] = export_memo
                
                            except Exception as e:
                                st.error(f"Failed to generate AI memo: {str(e)}")
                
                with col2:
                    if st.button("💾 Save Memo to Case"):
                        if case_id:
                            from datetime import datetime
                            
                            # Create descriptive memo name with timestamp
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                            if memo_name:
                                full_memo_name = f"{memo_name} ({timestamp})"
                            else:
                                full_memo_name = f"Memo - {timestamp}"
                            
                            # Save AI-enhanced version if it exists, otherwise save the base memo
                            memo_to_save = st.session_state.get("enhanced_memo_export", edited_summary)
                            
                            # Add file count to memo metadata
                            memo_metadata = f"\n\n---\nGenerated: {timestamp}\nFiles included: {len(memo_data['files'])}\nType: {'AI-Enhanced' if 'enhanced_memo_export' in st.session_state else 'Basic'}"
                            memo_with_metadata = memo_to_save + memo_metadata
                            
                            save_memo(case_id.strip(), memo_with_metadata, sources=memo_data['files'], memo_name=full_memo_name)
                            
                            st.success(f"✅ Memo '{full_memo_name}' saved to case: {case_id.strip()}")
                        else:
                            st.warning("⚠️ Please enter a case ID to save")

                if "enhanced_memo_display" in st.session_state:
                    st.subheader("🧠 AI-Enhanced Memo")
                    # Display rendered markdown instead of text area
                    st.markdown(st.session_state["enhanced_memo_display"])
                    
                    # Option to edit if needed
                    if st.checkbox("✏️ Edit enhanced memo"):
                        edited_enhanced = st.text_area(
                            "Edit enhanced memo:", 
                            value=st.session_state["enhanced_memo_display"], 
                            height=300
                        )
                        # Update both versions if edited
                        if edited_enhanced != st.session_state["enhanced_memo_display"]:
                            st.session_state["enhanced_memo_display"] = edited_enhanced
                            # Convert edited version to export format (remove markdown)
                            import re
                            export_version = re.sub(r'#+\s*', '', edited_enhanced)  # Remove # headers
                            export_version = re.sub(r'\*\*(.*?)\*\*', r'\1', export_version)  # Remove bold
                            export_version = re.sub(r'##\s*', '', export_version)  # Remove remaining headers
                            st.session_state["enhanced_memo_export"] = export_version

                # Export options
                st.subheader("📤 Export Options")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📄 Export as .txt"):
                        from datetime import datetime
                        memo_part = memo_name.replace(' ', '_') if memo_name else 'general'
                        filename = f"memo_{memo_part}_{case_id or 'nocase'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        
                        # Use export version (no markdown) if available, otherwise use edited summary
                        content = st.session_state.get("enhanced_memo_export", edited_summary)
                        
                        with open(filename, "w") as f:
                            f.write(content)
                        st.success(f"Exported as {filename}")

                with col2:
                    if st.button("📄 Export as .docx"):
                        from datetime import datetime
                        memo_part = memo_name.replace(' ', '_') if memo_name else 'general'
                        filename = f"memo_{memo_part}_{case_id or 'nocase'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                        downloads_folder = Path(os.path.expanduser("~/Downloads/ofw"))
                        downloads_folder.mkdir(parents=True, exist_ok=True)
                        output_path = downloads_folder / filename
                        
                        # Use export version (no markdown) for docx
                        content = st.session_state.get("enhanced_memo_export", edited_summary)
                        export_memo_docx(case_id or "General", content, output_path)
                        st.success(f"Exported to {output_path}")

                with col3:
                    if st.button("🔄 Clear Memo"):
                        keys_to_remove = ["memo_content", "enhanced_memo_display", "enhanced_memo_export"]
                        for key in keys_to_remove:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

        # Display saved memos
        st.subheader("📂 Saved Memos")
        from app.utils.memo import load_memos
        saved_memos = load_memos()
        
        if saved_memos:
            for cid, memo_data in saved_memos.items():
                # Handle both old format (single memo) and new format (list of memos)
                if isinstance(memo_data, list):
                    memo_list = memo_data
                else:
                    # Convert old format to new format
                    memo_list = [memo_data]
                
                with st.expander(f"📋 Case: {cid} ({len(memo_list)} memo(s))"):
                    for i, memo_obj in enumerate(memo_list):
                        memo_name = memo_obj.get("memo_name", f"Memo {i+1}")
                        memo_text = memo_obj.get("memo_text", "")
                        sources = memo_obj.get("sources", [])
                        
                        st.markdown(f"**{memo_name}**")
                        st.text_area("", value=memo_text[:300] + ("..." if len(memo_text) > 300 else ""), 
                                height=100, disabled=True, key=f"preview_{cid}_{i}")
                        
                        if sources:
                            st.markdown(f"*Sources: {', '.join(sources[:3])}{'...' if len(sources) > 3 else ''}*")
                        
                        # Export buttons for each memo
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Export as .txt", key=f"{cid}_{i}_txt"):
                                from datetime import datetime
                                safe_name = memo_name.replace(' ', '_')
                                filename = f"{safe_name}_{cid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                                with open(filename, "w") as f:
                                    f.write(memo_text)
                                st.success(f"Exported as {filename}")

                        with col2:
                            if st.button("Export as .docx", key=f"{cid}_{i}_docx"):
                                from datetime import datetime
                                safe_name = memo_name.replace(' ', '_')
                                filename = f"{safe_name}_{cid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                                downloads_folder = Path(os.path.expanduser("~/Downloads/ofw"))
                                downloads_folder.mkdir(parents=True, exist_ok=True)
                                output_path = downloads_folder / filename
                                export_memo_docx(cid, memo_text, output_path)
                                st.success(f"Exported to {output_path}")
                        
                        if i < len(memo_list) - 1:  # Add separator between memos
                            st.markdown("---")
        else:
            st.info("No saved memos yet. Create one above!")



if __name__ == "__main__":
    main()
