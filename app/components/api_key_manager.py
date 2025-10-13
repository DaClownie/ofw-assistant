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
        st.markdown("### 🔑 Welcome to OFW Assistant")
        st.markdown("To get started, you'll need an OpenAI API key.")
        st.markdown("**[Get your API key from OpenAI →](https://platform.openai.com/api-keys)**")
        st.markdown("---")
        
        with st.form("api_key_form"):
            st.write("Enter your OpenAI API Key below:")
            
            # Disable password managers with autocomplete="off"
            api_key_input = st.text_input(
                "API Key", 
                type="password",
                help="Paste your OpenAI API key here. It will be stored locally in a .env file.",
                placeholder="sk-..."
            )
            
            # Add custom CSS to disable autocomplete
            st.markdown("""
            <style>
            /* Disable password manager autofill */
            input[type="password"] {
                autocomplete: new-password !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Save API Key", type="primary")
            
            if submitted:
                if api_key_input.strip():
                    ENV_PATH.write_text(f"OPENAI_API_KEY={api_key_input.strip()}")
                    st.success("✅ API key saved successfully!")
                    st.info("👇 Click the button below to reload the app")
                    
                    # Add reload button
                    if st.button("🔄 Reload Application", type="primary"):
                        st.rerun()
                    
                    st.stop()
                else:
                    st.error("❌ Please enter a valid API key")
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
                        st.text_input("Current Key:", value=masked_key, disabled=True, label_visibility="visible")
            except:
                st.text_input("Current Key:", value="[Error reading key]", disabled=True, label_visibility="visible")
        else:
            st.text_input("Current Key:", value="No key set", disabled=True, label_visibility="visible")

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