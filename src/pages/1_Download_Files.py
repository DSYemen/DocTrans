import streamlit as st
import os
from pathlib import Path
import yaml
from urllib.parse import urlparse
from dotenv import load_dotenv

from config import AppConfig
from github_service import GitHubService
from translation_service import TranslationService
from llm_factory import LLMFactory

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Download Files - AI Documentation Translator",
    page_icon="📥",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables."""
    if 'base_input_dir' not in st.session_state:
        st.session_state.base_input_dir = "input_files"

def parse_github_url(url: str) -> tuple:
    """Parse GitHub URL to extract owner, repo, branch, and path."""
    try:
        # Parse URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Extract basic components
        owner = path_parts[0]
        repo = path_parts[1]
        
        # Handle different URL formats
        if 'tree' in path_parts:
            # URL format: github.com/owner/repo/tree/branch/path
            tree_index = path_parts.index('tree')
            branch = path_parts[tree_index + 1]
            folder_path = '/'.join(path_parts[tree_index + 2:]) if len(path_parts) > tree_index + 2 else ""
        elif 'blob' in path_parts:
            # URL format: github.com/owner/repo/blob/branch/path
            blob_index = path_parts.index('blob')
            branch = path_parts[blob_index + 1]
            folder_path = '/'.join(path_parts[blob_index + 2:]) if len(path_parts) > blob_index + 2 else ""
        else:
            # Default to main branch if not specified
            branch = "main"
            folder_path = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ""
        
        return owner, repo, branch, folder_path
    except Exception as e:
        raise ValueError(f"Invalid GitHub URL format: {str(e)}")

def main():
    initialize_session_state()
    
    st.title("📥 Download Files from GitHub")
    st.markdown("Enter a GitHub URL to download documentation files")
    
    # GitHub configuration
    github_token = st.text_input(
        "GitHub Token (optional)",
        type="password",
        value=os.getenv("GITHUB_TOKEN", ""),
        help="Required for private repositories"
    )
    
    # URL input
    repo_url = st.text_input(
        "GitHub URL",
        placeholder="https://github.com/owner/repo/tree/branch/path",
        help="Enter a GitHub repository URL. The branch and path will be automatically extracted."
    )
    
    if repo_url:
        try:
            # Parse URL and extract components
            owner, repo_name, branch, folder_path = parse_github_url(repo_url)
            
            # Show extracted information
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📦 Repository: {owner}/{repo_name}")
                st.info(f"🌿 Branch: {branch}")
            with col2:
                st.info(f"📁 Path: {'/' + folder_path if folder_path else 'Root'}")
            
            # Fetch files button
            if st.button("Fetch Files", type="primary"):
                try:
                    with st.spinner("Fetching files from repository..."):
                        github_service = GitHubService(github_token)
                        
                        files = github_service.get_repository_files(
                            repo_url=f"https://github.com/{owner}/{repo_name}",
                            branch=branch,
                            folder_path=folder_path,
                            file_types=AppConfig.supported_file_types
                        )
                        
                        if not files:
                            st.warning("No supported files found in the specified path.")
                            return
                        
                        # Download files
                        downloaded_files = []
                        progress_text = st.empty()
                        progress_bar = st.progress(0)
                        
                        for i, file in enumerate(files, 1):
                            progress_text.text(f"Downloading: {file.path}")
                            local_path = github_service.download_file(
                                file,
                                st.session_state.base_input_dir,
                                owner,
                                repo_name,
                                branch,
                                folder_path
                            )
                            downloaded_files.append({
                                'path': local_path,
                                'name': file.path
                            })
                            progress_bar.progress(i / len(files))
                        
                        folder_name = f"{owner}_{repo_name}_{branch}"
                        if folder_path:
                            folder_name += f"_{folder_path.replace('/', '_')}"
                        
                        st.success(f"Successfully downloaded {len(files)} files to {folder_name}!")
                        
                        # Display downloaded files
                        with st.expander("📥 Downloaded Files", expanded=True):
                            for file in downloaded_files:
                                st.text(f"✓ {file['name']}")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        
        except ValueError as e:
            st.error(str(e))

if __name__ == "__main__":
    main()
