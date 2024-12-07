import os
import shutil
import streamlit as st
from pathlib import Path
import yaml
from dotenv import load_dotenv

from config import AppConfig
from github_service import GitHubService
from translation_service import TranslationService
from llm_factory import LLMFactory

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Documentation Translator",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 AI Documentation Translator")
st.markdown("""
Welcome to the AI Documentation Translator! This tool helps you translate technical documentation from GitHub repositories into Arabic.

### Features:
- Download files from GitHub repositories
- Translate documentation using various LLM providers
- Upload translated files back to GitHub
- Support for multiple file formats (.md, .mdx, .rst, .py, .html)

### Getting Started:
1. Navigate to the **Download Files** page to fetch documentation from GitHub
2. Use the **Translate Files** page to select and translate downloaded files
3. Upload completed translations using the **Upload Translations** page

### Navigation:
- 📥 **Download Files**: Fetch documentation from GitHub
- 🔄 **Translate Files**: Select and translate downloaded files
- ⬆️ **Upload Translations**: Push translated files to GitHub
""")

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
    .file-list {
        margin: 1rem 0;
        padding: 1rem;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

def load_glossary(file_path: str) -> dict:
    """Load translation glossary from YAML file."""
    if not file_path or not os.path.exists(file_path):
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def initialize_session_state():
    """Initialize session state variables."""
    if 'downloaded_files' not in st.session_state:
        st.session_state.downloaded_files = []
    if 'base_input_dir' not in st.session_state:
        st.session_state.base_input_dir = "input_files"
    if 'base_output_dir' not in st.session_state:
        st.session_state.base_output_dir = "output_files"

def cleanup_translated_file(file_path: str):
    """Remove file after translation."""
    try:
        os.remove(file_path)
        # Remove empty parent directories
        parent = os.path.dirname(file_path)
        while parent and not os.listdir(parent):
            os.rmdir(parent)
            parent = os.path.dirname(parent)
    except Exception as e:
        st.warning(f"Could not remove temporary file {file_path}: {str(e)}")

def main():
    initialize_session_state()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
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
        
        # GitHub configuration
        github_token = st.text_input(
            "GitHub Token (optional)",
            type="password",
            value=os.getenv("GITHUB_TOKEN", "")
        )
        
        # Glossary file
        glossary_file = st.file_uploader(
            "Upload Translation Glossary (YAML)",
            type=['yaml', 'yml']
        )

    # Main content
    col1, col2 = st.columns(2)
    with col1:
        repo_url = st.text_input("GitHub Repository URL")
        branch = st.text_input("Branch", value="main")
    with col2:
        folder_path = st.text_input("Folder Path", placeholder="docs/folder/")
        file_path = st.text_input("File Path (optional)", placeholder="specific-file.md")
    
    # Input/Output directory configuration
    if repo_url:
        try:
            github_service = GitHubService(github_token)
            _, repo_name = github_service.get_repository_info(repo_url)
            
            col1, col2 = st.columns(2)
            with col1:
                download_folder = st.text_input(
                    "Download Folder Name",
                    value=repo_name,
                    help="Folder name under input_files/"
                )
            with col2:
                translation_folder = st.text_input(
                    "Translation Output Folder",
                    value=repo_name,
                    help="Folder name under output_files/"
                )
        except Exception as e:
            st.error(f"Invalid repository URL: {str(e)}")
            return
    
    # Fetch files button
    if st.button("Fetch Files", type="secondary"):
        if not repo_url:
            st.error("Please enter a GitHub repository URL.")
            return
            
        try:
            with st.spinner("Fetching files from repository..."):
                github_service = GitHubService(github_token)
                files = github_service.get_repository_files(
                    repo_url=repo_url,
                    branch=branch,
                    folder_path=folder_path,
                    file_path=file_path,
                    file_types=AppConfig.supported_file_types
                )
                
                if not files:
                    st.warning("No supported files found in the specified path.")
                    return
                
                # Download files
                st.session_state.downloaded_files = []
                for file in files:
                    local_path = github_service.download_file(
                        file,
                        st.session_state.base_input_dir,
                        download_folder
                    )
                    st.session_state.downloaded_files.append({
                        'path': local_path,
                        'name': file.path,
                        'selected': True
                    })
                
                st.success(f"Successfully fetched {len(files)} files!")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Display downloaded files
    if st.session_state.downloaded_files:
        st.subheader("Available Files")
        
        # Select/Deselect All
        col1, col2 = st.columns([1, 4])
        with col1:
            select_all = st.checkbox("Select All", value=True)
        
        # Update all checkboxes based on select_all
        if select_all:
            for file in st.session_state.downloaded_files:
                file['selected'] = True
        
        # File selection
        st.markdown("<div class='file-list'>", unsafe_allow_html=True)
        for file in st.session_state.downloaded_files:
            file['selected'] = st.checkbox(
                file['name'],
                value=file['selected']
            )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Translation button
        if st.button("Start Translation", type="primary"):
            if not translation_folder:
                st.error("Please specify a translation output folder name.")
                return
                
            try:
                selected_files = [f for f in st.session_state.downloaded_files 
                                if f['selected']]
                
                if not selected_files:
                    st.warning("Please select at least one file to translate.")
                    return
                
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
                            translation_folder
                        )
                        files_progress.success(
                            f"✅ Translated: {file_info['name']} → {output_path}"
                        )
                        
                        # Clean up translated file
                        cleanup_translated_file(file_info['path'])
                        st.session_state.downloaded_files.remove(file_info)
                        
                    except Exception as e:
                        files_progress.error(
                            f"❌ Error processing {file_info['name']}: {str(e)}"
                        )
                    
                    # Update progress
                    progress_bar.progress(i / total_files)
                
                st.success(f"Translation completed! Check {st.session_state.base_output_dir}/{translation_folder} for translated files.")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
