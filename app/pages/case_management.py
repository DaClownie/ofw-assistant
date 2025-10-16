"""
Case Management page for managing cases, files, and exports
"""
import streamlit as st
from app.utils.case_manager import CaseManager
from app.utils.memory import get_cases


def _render_folder_migration_check(manager):
    """Check if any folders need normalization and offer to fix them"""
    case_files_dir = manager.case_files_dir
    
    if not case_files_dir.exists():
        return
    
    # Check for folders with spaces
    folders_with_spaces = []
    for folder in case_files_dir.iterdir():
        if folder.is_dir() and ' ' in folder.name:
            folders_with_spaces.append(folder.name)
    
    if folders_with_spaces:
        st.warning("⚠️ **Folder Naming Issue Detected**")
        st.markdown(f"Found {len(folders_with_spaces)} case folder(s) with spaces in their names. "
                   "This can cause issues with terminal commands and file operations.")
        
        with st.expander("🔧 View Affected Folders"):
            for folder_name in folders_with_spaces:
                normalized = folder_name.replace(' ', '_')
                st.markdown(f"- `{folder_name}` → `{normalized}`")
        
        st.info("💡 Click below to automatically rename all folders to use underscores (recommended)")
        
        if st.button("✨ Normalize All Folder Names", type="primary"):
            with st.spinner("Normalizing folder names..."):
                results = manager.normalize_all_folders()
            
            if results['renamed'] > 0:
                st.success(f"✅ Successfully normalized {results['renamed']} folder(s)")
            
            if results['already_normalized'] > 0:
                st.info(f"ℹ️ {results['already_normalized']} folder(s) already normalized")
            
            if results['errors']:
                st.error("❌ Some folders could not be renamed:")
                for error in results['errors']:
                    st.markdown(f"- {error}")
            
            if results['renamed'] > 0:
                st.info("🔄 Refreshing page...")
                st.rerun()
        
        st.markdown("---")


def render_case_management_page():
    """Render the case management page UI"""
    st.header("📁 Case Management")
    
    manager = CaseManager()
    
    # Check for folders that need normalization
    _render_folder_migration_check(manager)
    
    cases = get_cases()
    
    if not cases:
        st.info("No cases found. Upload files to a case first.")
        return
    
    # Case selector
    st.subheader("Select a Case")
    selected_case = st.selectbox(
        "Choose a case to manage:",
        cases,
        label_visibility="collapsed"
    )
    
    if not selected_case:
        return
    
    # Get case stats
    stats = manager.get_case_stats(selected_case)
    
    if not stats['exists']:
        st.error(f"Case '{selected_case}' not found")
        return
    
    # Display case overview
    _render_case_overview(selected_case, stats)
    
    st.markdown("---")
    
    # Case actions
    st.subheader("⚙️ Case Actions")
    
    # Create tabs for different operations
    action_tabs = st.tabs(["📦 Export", "✏️ Rename", "🗑️ Delete"])
    
    with action_tabs[0]:
        _render_export_section(selected_case, stats, manager)
    
    with action_tabs[1]:
        _render_rename_section(selected_case, manager)
    
    with action_tabs[2]:
        _render_delete_section(selected_case, stats, manager)


def _render_case_overview(case_id, stats):
    """Render case overview statistics"""
    st.subheader(f"📊 Case Overview: {case_id}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Files", stats['file_count'])
    col2.metric("Transcripts", stats['transcript_count'])
    col3.metric("Flags", stats['flag_count'])
    col4.metric("Tags", len(stats['tags']))
    
    # Show categories
    if stats['categories']:
        with st.expander("🏷️ View Tags by Category"):
            for category, tags in sorted(stats['categories'].items()):
                st.markdown(f"**{category.replace('_', ' ').title()}** ({len(tags)} tags)")
                st.markdown(f"  {', '.join(sorted(tags))}")
    
    # Show creation date if available
    if stats['created_date']:
        st.caption(f"Created: {stats['created_date']}")


def _render_export_section(case_id, stats, manager):
    """Render export options"""
    st.markdown("### 📦 Export Files")
    st.markdown("Export files as a zip archive for sharing or archival purposes.")
    
    export_option = st.radio(
        "Export options:",
        ["Entire Case", "By Category", "By Specific Tags"],
        label_visibility="collapsed"
    )
    
    if export_option == "Entire Case":
        st.info(f"This will export all {stats['file_count']} files from this case.")
        
        if st.button("📥 Download Complete Case", type="primary"):
            with st.spinner("Creating zip file..."):
                success, path, message = manager.export_case(case_id)
            
            if success:
                st.success(f"✅ {message}")
                st.info(f"📁 Saved to: {path}")
            else:
                st.error(f"❌ {message}")
    
    elif export_option == "By Category":
        if not stats['categories']:
            st.warning("No categories found in this case.")
            return
        
        category_options = [
            f"{cat.replace('_', ' ').title()} ({len(tags)} tags)"
            for cat, tags in sorted(stats['categories'].items())
        ]
        
        selected_category_label = st.selectbox(
            "Select category:",
            category_options
        )
        
        # Extract category name from label
        selected_category = selected_category_label.split(' (')[0].lower().replace(' ', '_')
        
        # Count files in this category
        category_file_count = 0
        for fname, meta in stats['files']:
            for tag in meta.get('tags', []):
                from app.utils.controlled_taxonomy import controlled_taxonomy
                if controlled_taxonomy.get_category_for_tag(tag) == selected_category:
                    category_file_count += 1
                    break
        
        st.info(f"This will export {category_file_count} files from '{selected_category_label.split(' (')[0]}'")
        
        if st.button("📥 Download Category", type="primary"):
            with st.spinner("Creating zip file..."):
                success, path, message = manager.export_by_category(case_id, selected_category)
            
            if success:
                st.success(f"✅ {message}")
                st.info(f"📁 Saved to: {path}")
            else:
                st.error(f"❌ {message}")
    
    elif export_option == "By Specific Tags":
        if not stats['tags']:
            st.warning("No tags found in this case.")
            return
        
        # Create tag options with counts
        tag_counts = {}
        for fname, meta in stats['files']:
            for tag in meta.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        tag_options = [
            f"{tag.replace('_', ' ')} ({tag_counts[tag]} files)"
            for tag in sorted(stats['tags'])
        ]
        
        selected_tag_labels = st.multiselect(
            "Select tags (files matching ANY tag will be included):",
            tag_options
        )
        
        if selected_tag_labels:
            # Extract tag names from labels
            selected_tags = [label.split(' (')[0].replace(' ', '_') for label in selected_tag_labels]
            
            # Count matching files
            matching_count = 0
            for fname, meta in stats['files']:
                file_tags = set(meta.get('tags', []))
                if file_tags.intersection(set(selected_tags)):
                    matching_count += 1
            
            st.info(f"This will export {matching_count} files matching {len(selected_tags)} tag(s)")
            
            if st.button("📥 Download Tagged Files", type="primary"):
                with st.spinner("Creating zip file..."):
                    success, path, message = manager.export_by_tags(case_id, selected_tags)
                
                if success:
                    st.success(f"✅ {message}")
                    st.info(f"📁 Saved to: {path}")
                else:
                    st.error(f"❌ {message}")
        else:
            st.info("👆 Select one or more tags to export")


def _render_rename_section(case_id, manager):
    """Render rename case functionality"""
    st.markdown("### ✏️ Rename Case")
    st.markdown("Change the case identifier. This will update all associated files and metadata.")
    
    new_name = st.text_input(
        "New case name:",
        placeholder="Enter new case identifier",
        help="Choose a unique identifier for this case"
    )
    
    if new_name and new_name != case_id:
        st.info(f"Case will be renamed from '{case_id}' to '{new_name}'")
        
        if st.button("✅ Confirm Rename", type="primary"):
            with st.spinner("Renaming case..."):
                success, message = manager.rename_case(case_id, new_name)
            
            if success:
                st.success(f"✅ {message}")
                st.info("🔄 Refreshing page...")
                st.rerun()
            else:
                st.error(f"❌ {message}")
    elif new_name == case_id:
        st.warning("New name must be different from current name")


def _render_delete_section(case_id, stats, manager):
    """Render delete case functionality"""
    st.markdown("### 🗑️ Delete Case")
    st.markdown("⚠️ **Warning:** This action cannot be undone!")
    
    # Check if can delete
    can_delete, error_msg = manager.can_delete_case(case_id)
    
    if not can_delete:
        st.error(f"❌ Cannot delete case: {error_msg}")
        return
    
    # Show what will be deleted
    st.warning("This will permanently delete:")
    st.markdown(f"- **{stats['file_count']} files** from local storage")
    st.markdown(f"- All tags and metadata")
    st.markdown(f"- Processing history")
    st.markdown("")
    st.info("ℹ️ Downloaded memos in ~/Downloads/ofw/ will NOT be deleted")
    
    # Confirmation checkbox
    confirm = st.checkbox(
        f"I understand this will permanently delete case '{case_id}' and all its files",
        key=f"confirm_delete_{case_id}"
    )
    
    if confirm:
        # Type case name to confirm
        typed_name = st.text_input(
            f"Type the case name '{case_id}' to confirm deletion:",
            placeholder=case_id,
            help="This ensures you're deleting the correct case"
        )
        
        if typed_name == case_id:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("🗑️ Delete Case", type="primary"):
                    with st.spinner("Deleting case..."):
                        success, message = manager.delete_case(case_id)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info("🔄 Refreshing page...")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            with col2:
                st.caption("Click to permanently delete")
        elif typed_name:
            st.error("❌ Case name doesn't match")
    else:
        st.info("👆 Check the box above to proceed with deletion")