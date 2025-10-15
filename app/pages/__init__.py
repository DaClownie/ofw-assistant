"""
Pages package for main application views
"""
from .upload import render_upload_page
from .dashboard import render_dashboard_page
from .memo_builder import render_memo_builder_page
from .case_management import render_case_management_page

__all__ = [
    'render_upload_page',
    'render_dashboard_page',
    'render_memo_builder_page',
    'render_case_management_page'
]