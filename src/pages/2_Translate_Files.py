import streamlit as st
import os
from pathlib import Path
import yaml
import shutil
from dotenv import load_dotenv

from config import AppConfig
from translation_service import TranslationService
from llm_factory import LLMFactory

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Translate Files - AI Documentation Translator",
    page_icon="🔄",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .file-list {
        margin: 1rem 0;
        padding: 1rem;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
    }
    .delete-button {
        color: #dc3545;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'base_input_dir' not in st.session_state:
        st.session_state.base_input_dir = "input_files"
    if 'base_output_dir' not in st.session_state:
        st.session_state.base_output_dir = "output_files"

def get_downloaded_files():
    """Get all downloaded files from input directory."""
    input_dir = Path(st.session_state.base_input_dir)
    if not input_dir.exists():
        return []
    
    files = []
    for repo_dir in input_dir.iterdir():
        if repo_dir.is_dir():
            for file_path in repo_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.md', '.mdx', '.rst', '.rstx', '.py', '.html']:
                    files.append({
                        'path': str(file_path),
                        'name': str(file_path.relative_to(input_dir)),
                        'repo': repo_dir.name
                    })
    return files

def delete_file(file_path: str):
    """Delete a file and its empty parent directories."""
    try:
        os.remove(file_path)
        parent = os.path.dirname(file_path)
        while parent and not os.listdir(parent):
            os.rmdir(parent)
            parent = os.path.dirname(parent)
        return True
    except Exception as e:
        st.error(f"Error deleting file: {str(e)}")
        return False

def main():
    initialize_session_state()
    
    st.title("🔄 Translate Downloaded Files")
    st.markdown("Select and translate downloaded documentation files")
    
    # LLM Configuration
    with st.sidebar:
        st.header("Translation Settings")
        
        # LLM Selection
        llm_provider = st.selectbox(
            "Select LLM Provider",
            ["gemini", "cohere", "groq", "together"],
            index=0
        )
        
        api_key = st.text_input(
            f"{llm_provider.title()} API Key",
            type="password",
            value=os.getenv(f"{llm_provider.upper()}_API_KEY", "")
        )
        
        # Available models for selected provider
        models = LLMFactory.get_available_models()[llm_provider]
        model_name = st.selectbox("Select Model", models)
        
        # Glossary file
        glossary_file = st.file_uploader(
            "Upload Translation Glossary (YAML)",
            type=['yaml', 'yml']
        )
    
    # Get downloaded files
    files = get_downloaded_files()
    
    if not files:
        st.warning("No files found in input directory. Please download some files first.")
        return
    
    # Group files by repository folder
    repos = {}
    for file in files:
        if file['repo'] not in repos:
            repos[file['repo']] = []
        repos[file['repo']].append(file)
    
    # Display files by repository in expandable sections
    for repo_name, repo_files in repos.items():
        with st.expander(f"📁 {repo_name} ({len(repo_files)} files)", expanded=True):
            # Select all for this repo
            col1, col2 = st.columns([1, 4])
            with col1:
                select_all = st.checkbox(f"Select All", key=f"select_all_{repo_name}")
            
            # File selection
            selected_files = []
            for file in repo_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    selected = st.checkbox(
                        "📄 " + os.path.basename(file['path']),
                        value=select_all,
                        key=f"file_{file['path']}"
                    )
                    if selected:
                        selected_files.append(file)
                with col2:
                    if st.button("🗑️", key=f"delete_{file['path']}", help="Delete file"):
                        if delete_file(file['path']):
                            st.rerun()
            
            # Translation button for this repo
            if selected_files:
                st.markdown("---")
                if st.button(f"Translate Selected Files ({len(selected_files)})", key=f"translate_{repo_name}"):
                    try:
                        with st.spinner("Setting up translation service..."):
                            # Create LLM instance
                            llm = LLMFactory.create_llm(
                                llm_provider,
                                api_key,
                                model_name=model_name
                            )
                            
                            # Load glossary if provided
                            glossary = {}
                            if glossary_file:
                                glossary_content = glossary_file.read().decode()
                                glossary = yaml.safe_load(glossary_content)
                            
                            translation_service = TranslationService(llm, glossary)
                        
                        # Create progress containers
                        files_progress = st.empty()
                        current_file = st.empty()
                        progress_bar = st.progress(0)
                        
                        # Process files
                        total_files = len(selected_files)
                        for i, file_info in enumerate(selected_files, 1):
                            current_file.text(f"Processing: {file_info['name']}")
                            
                            try:
                                # Translate file
                                output_path = translation_service.process_file(
                                    file_info['path'],
                                    st.session_state.base_output_dir,
                                    repo_name
                                )
                                files_progress.success(
                                    f"✅ Translated: {file_info['name']} → {output_path}"
                                )
                                
                                # Delete input file after successful translation
                                delete_file(file_info['path'])
                                
                            except Exception as e:
                                files_progress.error(
                                    f"❌ Error processing {file_info['name']}: {str(e)}"
                                )
                            
                            # Update progress
                            progress_bar.progress(i / total_files)
                        
                        st.success(f"Translation completed! Check {st.session_state.base_output_dir}/{repo_name} for translated files.")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
