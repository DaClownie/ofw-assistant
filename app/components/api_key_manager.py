"""
API Key management component for sidebar
"""
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from app.config import ENV_PATH


def ensure_api_key():
    """Check if API key exists, prompt user if not"""
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


def render_api_key_expander():
    """Render API key management in sidebar expander"""
    with st.sidebar.expander("🔑 API Key Management"):
        # Current API key status
        if ENV_PATH.exists():
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
        st.markdown("[Get OpenAI API Key](https://platform.openai.com/api-keys)")
        
        new_api_key = st.text_input(
            "New API Key:", 
            type="password", 
            help="Enter your OpenAI API key"
        )
            
        if st.button("Update Key"):
            if new_api_key.strip():
                try:
                    ENV_PATH.write_text(f"OPENAI_API_KEY={new_api_key.strip()}")
                    st.success("API key updated! Please refresh the page.")
                    load_dotenv(dotenv_path=ENV_PATH, override=True)
                except Exception as e:
                    st.error(f"Failed to update API key: {e}")
            else:
                st.warning("Please enter a valid API key")