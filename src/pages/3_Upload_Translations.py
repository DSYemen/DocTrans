import streamlit as st
import os
from pathlib import Path
from github import Github, GithubException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Upload Translations - AI Documentation Translator",
    page_icon="⬆️",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables."""
    if 'base_output_dir' not in st.session_state:
        st.session_state.base_output_dir = "output_files"

def get_translated_files():
    """Get all translated files from output directory."""
    output_dir = Path(st.session_state.base_output_dir)
    if not output_dir.exists():
        return []
    
    files = []
    for repo_dir in output_dir.iterdir():
        if repo_dir.is_dir():
            for file_path in repo_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.md', '.mdx', '.rst', '.rstx', '.py', '.html']:
                    files.append({
                        'path': str(file_path),
                        'name': file_path.name,
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

def upload_to_github(repo, file_info: dict, target_path: str, branch: str) -> bool:
    """Upload a file to GitHub repository."""
    try:
        # Read file content with UTF-8 encoding
        with open(file_info['path'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get just the filename from the full path
        file_name = os.path.basename(file_info['path'])
        
        # Create the target path in the repository
        if target_path:
            repo_file_path = f"{target_path}/{file_name}"
        else:
            repo_file_path = file_name
        
        # Remove any leading/trailing slashes
        repo_file_path = repo_file_path.strip('/')
        
        # Create commit message
        commit_message = f"Add translated file: {file_name}"
        
        try:
            # Check if file exists
            try:
                contents = repo.get_contents(repo_file_path, ref=branch)
                repo.update_file(
                    contents.path,
                    commit_message,
                    content,
                    contents.sha,
                    branch=branch
                )
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(
                    repo_file_path,
                    commit_message,
                    content,
                    branch=branch
                )
            
            return True
            
        except GithubException as e:
            st.error(f"GitHub API Error: {str(e)}")
            if hasattr(e, 'data') and 'message' in e.data:
                st.error(f"GitHub says: {e.data['message']}")
            return False
            
    except Exception as e:
        st.error(f"Error uploading {file_info['name']}: {str(e)}")
        return False

def main():
    initialize_session_state()
    
    st.title("⬆️ Upload Translations to GitHub")
    st.markdown("Enter a GitHub URL to upload translated files")
    
    # GitHub configuration
    github_token = st.text_input(
        "GitHub Token (required)",
        type="password",
        value=os.getenv("GITHUB_TOKEN", ""),
        help="Required for uploading files"
    )
    
    if not github_token:
        st.error("GitHub token is required for uploading files.")
        return
    
    # URL input
    repo_url = st.text_input(
        "Target GitHub URL",
        placeholder="https://github.com/owner/repo/tree/branch/path",
        help="Enter the GitHub URL where you want to upload the translations"
    )
    
    # Delete after upload option
    delete_after_upload = st.checkbox("Delete files after successful upload", value=True)
    
    if repo_url:
        try:
            # Clean up the repository URL
            if 'github.com' in repo_url:
                repo_url = repo_url.split('github.com/')[-1]
            repo_url = repo_url.strip('/')
            
            # Parse URL components
            parts = repo_url.split('/')
            if len(parts) < 2:
                st.error("Invalid GitHub URL. Must contain owner and repository name.")
                return
            
            owner = parts[0]
            repo_name = parts[1]
            
            # Handle tree/blob paths
            if len(parts) > 2 and parts[2] in ['tree', 'blob']:
                branch = parts[3]
                folder_path = '/'.join(parts[4:]) if len(parts) > 4 else ""
            else:
                branch = "main"
                folder_path = '/'.join(parts[2:]) if len(parts) > 2 else ""
            
            # Show extracted information
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📦 Repository: {owner}/{repo_name}")
                st.info(f"🌿 Branch: {branch}")
            with col2:
                st.info(f"📁 Upload Path: {'/' + folder_path if folder_path else 'Root'}")
            
            # Get translated files
            files = get_translated_files()
            
            if not files:
                st.warning("No translated files found in output directory.")
                return
            
            # Group files by repository folder
            repos = {}
            for file in files:
                if file['repo'] not in repos:
                    repos[file['repo']] = []
                repos[file['repo']].append(file)
            
            # Display files by repository in expandable sections
            for repo_folder, repo_files in repos.items():
                with st.expander(f"📁 {repo_folder} ({len(repo_files)} files)", expanded=True):
                    # Select all for this repo
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        select_all = st.checkbox(f"Select All", key=f"select_all_{repo_folder}")
                    
                    # File selection
                    selected_files = []
                    for file in repo_files:
                        col1, col2 = st.columns([4, 1])
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
                    
                    # Upload button for this repo
                    if selected_files:
                        st.markdown("---")
                        if st.button(f"Upload Selected Files ({len(selected_files)})", key=f"upload_{repo_folder}"):
                            try:
                                # Initialize GitHub with explicit error handling
                                try:
                                    g = Github(github_token)
                                    repo = g.get_repo(f"{owner}/{repo_name}")
                                except Exception as e:
                                    st.error(f"Error accessing repository: {str(e)}")
                                    st.error(f"Please check if:\n1. Your GitHub token is valid\n2. You have access to {owner}/{repo_name}\n3. The repository exists and is spelled correctly")
                                    return
                                
                                # Create progress containers
                                progress_text = st.empty()
                                progress_bar = st.progress(0)
                                files_progress = st.container()
                                
                                # Upload files
                                total_files = len(selected_files)
                                successful_uploads = 0
                                
                                for i, file_info in enumerate(selected_files, 1):
                                    progress_text.text(f"Uploading: {file_info['name']}")
                                    
                                    try:
                                        if upload_to_github(repo, file_info, folder_path, branch):
                                            with files_progress:
                                                st.success(f"✅ Uploaded: {file_info['name']}")
                                            successful_uploads += 1
                                            
                                            # Delete local file after successful upload if option is selected
                                            if delete_after_upload:
                                                delete_file(file_info['path'])
                                    except Exception as e:
                                        with files_progress:
                                            st.error(f"❌ Failed to upload {file_info['name']}: {str(e)}")
                                    
                                    # Update progress
                                    progress_bar.progress(i / total_files)
                                
                                progress_text.empty()
                                if successful_uploads == total_files:
                                    st.success(f"Successfully uploaded all {total_files} files!")
                                else:
                                    st.warning(f"Uploaded {successful_uploads} out of {total_files} files.")
                                
                                if successful_uploads > 0:
                                    st.rerun()
                            
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                                st.error("Please check your GitHub token and repository permissions.")
        
        except ValueError as e:
            st.error(str(e))

if __name__ == "__main__":
    main()
