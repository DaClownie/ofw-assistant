"""
Dashboard page for viewing case statistics, browsing files, and searching
"""
import streamlit as st
import pandas as pd
from app.utils.memory import get_cases, load_memory
from app.utils.controlled_taxonomy import controlled_taxonomy
from app.utils.controlled_smart_tagger import controlled_smart_tagger
from app.utils.vectorstore import search_similar


def render_dashboard_page(memory):
    """Render the dashboard page UI"""
    st.header("📊 Dashboard")
    
    _render_overview_stats(memory)
    _render_category_browser(memory)
    _render_case_browser(memory)
    _render_smart_search(memory)
    _render_analytics(memory)
    _render_vector_search()


def _render_overview_stats(memory):
    """Render overview statistics cards"""
    st.subheader("📊 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    total_files = len(memory)
    total_cases = len(get_cases())
    total_flags = sum(len(meta.get("flags", [])) for meta in memory.values())
    
    safety_files = sum(
        1 for meta in memory.values() 
        if any(controlled_taxonomy.get_category_for_tag(tag) == 'safety_concerns' 
               for tag in meta.get("tags", []))
    )
    
    col1.metric("Total Files", total_files)
    col2.metric("Active Cases", total_cases)
    col3.metric("Total Flags", total_flags)
    col4.metric("Safety Concerns", safety_files)


def _render_category_browser(memory):
    """Render category-based file browser"""
    st.subheader("🏷️ Browse by Category")
    
    category_data = _build_category_data(memory)
    
    # Display categories with priority order
    priority_categories = ['safety_concerns', 'fabricated_concerns', 'legal_process', 'mental_health']
    all_categories = priority_categories + [
        cat for cat in sorted(category_data.keys()) 
        if cat not in priority_categories
    ]
    
    for category in all_categories:
        if category in category_data:
            _render_category_section(category, category_data[category], priority_categories)


def _build_category_data(memory):
    """Build data structure grouping files by category and tag"""
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
    
    return category_data


def _render_category_section(category, tag_dict, priority_categories):
    """Render a single category section with its tags and files"""
    total_files = sum(len(files) for files in tag_dict.values())
    
    # Special styling for high-priority categories
    if category in priority_categories[:2]:
        icon = "🚨" if category == 'safety_concerns' else "⚠️"
    else:
        icon = "📂"
    
    with st.expander(f"{icon} {category.replace('_', ' ').title()} ({total_files} files)"):
        for tag, file_data in sorted(tag_dict.items()):
            st.markdown(f"**#{tag.replace('_', ' ')}** ({len(file_data)} files)")
            
            # Group by case
            by_case = _group_by_case(file_data)
            
            for case, items in sorted(by_case.items()):
                st.markdown(f"  📁 **Case: {case}**")
                for item in items[:3]:
                    flag_str = f" 🚩 {' / '.join(item['flags'])}" if item['flags'] else ""
                    st.markdown(f"    - {item['file']}{flag_str}")
                if len(items) > 3:
                    st.markdown(f"    - ... and {len(items) - 3} more files")


def _group_by_case(file_data):
    """Group file data by case ID"""
    by_case = {}
    for item in file_data:
        case = item['case_id']
        if case not in by_case:
            by_case[case] = []
        by_case[case].append(item)
    return by_case


def _render_individual_case(case_id, memory):
    """Render detailed view for a single case"""
    case_files = [(fname, meta) for fname, meta in memory.items() 
                  if meta.get("case_id") == case_id]
    
    if not case_files:
        st.info(f"No files found in case: {case_id}")
        return
    
    # Case overview stats
    col1, col2, col3 = st.columns(3)
    
    total_files = len(case_files)
    has_transcripts = sum(1 for fname, meta in case_files if meta.get("transcript"))
    total_flags = sum(len(meta.get("flags", [])) for fname, meta in case_files)
    
    col1.metric("Files", total_files)
    col2.metric("Transcripts", has_transcripts)
    col3.metric("Flags", total_flags)
    
    # Show case profile
    st.markdown("### 📊 Case Profile")
    all_tags = set()
    for fname, meta in case_files:
        all_tags.update(meta.get("tags", []))
    
    if all_tags:
        case_categories = {}
        for tag in all_tags:
            cat = controlled_taxonomy.get_category_for_tag(tag)
            case_categories.setdefault(cat, []).append(tag)
        
        for cat, tags in sorted(case_categories.items()):
            with st.expander(f"**{cat.replace('_', ' ').title()}** ({len(tags)} tags)"):
                for tag in sorted(tags):
                    # Count files with this tag
                    tag_file_count = sum(1 for fname, meta in case_files 
                                        if tag in meta.get("tags", []))
                    st.markdown(f"- {tag.replace('_', ' ')} ({tag_file_count} files)")
    else:
        st.info("No tags found for this case")
    
    # Show files
    st.markdown("### 📄 Files")
    for fname, meta in sorted(case_files, key=lambda x: x[0]):
        flags = meta.get("flags", [])
        flag_str = f" 🚩 {' / '.join(flags)}" if flags else ""
        file_type = "🎙️" if meta.get("transcript") else "📄"
        
        with st.expander(f"{file_type} {fname}{flag_str}"):
            # Show tags for this file
            file_tags = meta.get("tags", [])
            if file_tags:
                st.markdown("**Tags:**")
                file_tags_by_cat = {}
                for tag in file_tags:
                    cat = controlled_taxonomy.get_category_for_tag(tag)
                    file_tags_by_cat.setdefault(cat, []).append(tag)
                
                for cat, tags in sorted(file_tags_by_cat.items()):
                    st.markdown(f"- **{cat.replace('_', ' ').title()}:** {', '.join(tags)}")
            
            # Show flags if present
            if flags:
                st.markdown("**Flags:**")
                for flag in flags:
                    st.markdown(f"- 🚩 {flag.replace('_', ' ').title()}")
            
            # Show transcript preview if available
            if meta.get("transcript"):
                st.markdown("**Transcript Preview:**")
                preview = meta["transcript"][:200]
                st.text(preview + ("..." if len(meta["transcript"]) > 200 else ""))


def _render_case_browser(memory):
    """Render case-based file browser"""
    st.subheader("📁 Browse by Case")
    
    cases = list(get_cases())
    case_tabs = st.tabs(["All Cases"] + cases[:5])
    
    # All Cases tab
    with case_tabs[0]:
        for cid in cases:
            _render_case_summary(cid, memory)
    
    # Individual case tabs
    for idx, case_id in enumerate(cases[:5], start=1):
        with case_tabs[idx]:
            _render_individual_case(case_id, memory)


def _render_case_summary(case_id, memory):
    """Render summary for a single case"""
    case_files = [(fname, meta) for fname, meta in memory.items() 
                  if meta.get("case_id") == case_id]
    
    has_transcript = any(meta.get("transcript") for fname, meta in case_files)
    total_flags = sum(len(meta.get("flags", [])) for fname, meta in case_files)
    
    case_info = f"📁 **{case_id}** ({len(case_files)} files"
    if has_transcript:
        case_info += " 🎙️"
    if total_flags > 0:
        case_info += f" 🚩{total_flags}"
    case_info += ")"
    
    with st.expander(case_info):
        _render_case_details(case_files, memory)


def _render_case_details(case_files, memory):
    """Render detailed case information"""
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


def _render_smart_search(memory):
    """Render enhanced search functionality"""
    st.subheader("🔍 Smart Search")
    search_query = st.text_input("Search files, tags, or content:")
    
    if search_query:
        st.markdown(f"**Results for:** `{search_query}`")
        search_results = _perform_search(search_query, memory)
        _display_search_results(search_results)


def _perform_search(query, memory):
    """Perform comprehensive search across files"""
    search_lower = query.lower()
    results = []
    
    for fname, meta in memory.items():
        score = 0
        reasons = []
        
        # Search in tags
        matching_tags = [tag for tag in meta.get("tags", []) 
                        if search_lower in tag.lower()]
        if matching_tags:
            score += len(matching_tags) * 3
            reasons.append(f"Tags: {', '.join(matching_tags)}")
        
        # Search in flags
        matching_flags = [flag for flag in meta.get("flags", []) 
                         if search_lower in flag.lower()]
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
            results.append({
                'file': fname,
                'case_id': meta.get('case_id', 'Unassigned'),
                'score': score,
                'reasons': reasons,
                'flags': meta.get('flags', [])
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def _display_search_results(results):
    """Display search results"""
    if results:
        for result in results[:10]:
            flag_str = f" 🚩 {' / '.join(result['flags'])}" if result['flags'] else ""
            st.markdown(f"**{result['file']}** (Case: {result['case_id']}){flag_str}")
            st.markdown(f"  - {' | '.join(result['reasons'])}")
    else:
        st.info("No matches found.")


def _render_analytics(memory):
    """Render analytics charts"""
    st.subheader("📊 Analytics")
    
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


def _render_vector_search():
    """Render vector-based content search"""
    st.subheader("🔍 Content Search")
    query = st.text_input("Search stored content:")
    
    if query:
        results = search_similar(query)
        for doc in results:
            st.markdown(f"**Match:** {doc.page_content[:200]}...")