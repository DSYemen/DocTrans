from typing import List, Optional, Union, Tuple
import os
from pathlib import Path
from github import Github
from github.ContentFile import ContentFile
from github.Repository import Repository

class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.github = Github(token) if token else Github()
    
    def get_repository_info(self, repo_url: str) -> Tuple[Repository, str]:
        """Get repository object and name from URL."""
        if "github.com/" in repo_url:
            parts = repo_url.split("github.com/")[-1].split("/")
            owner, repo_name = parts[0], parts[1].replace(".git", "")
        else:
            raise ValueError("Invalid GitHub repository URL")
        
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        return repo, repo_name
    
    def get_repository_files(self, repo_url: str, branch: str, folder_path: str = "", file_path: str = "", file_types: tuple = None) -> List[ContentFile]:
        """Fetch specific files from a GitHub repository."""
        repo, _ = self.get_repository_info(repo_url)
        
        try:
            # Set the branch
            if branch:
                repo.get_branch(branch)  # Validate branch exists
            
            # If specific file is requested
            if file_path:
                full_path = os.path.join(folder_path, file_path) if folder_path else file_path
                content = repo.get_contents(full_path, ref=branch)
                return [content] if isinstance(content, ContentFile) else []
            
            # If directory is specified
            search_path = folder_path if folder_path else ""
            return self._get_files_recursive(repo, file_types, search_path, branch)
            
        except Exception as e:
            raise ValueError(f"Error accessing repository: {str(e)}")
    
    def download_file(self, file: ContentFile, base_input_dir: str, download_folder: str) -> str:
        """Download a single file from GitHub and return its local path."""
        # Create full path: base_input_dir/download_folder/file_path
        download_path = Path(base_input_dir) / download_folder
        local_path = download_path / file.path
        
        os.makedirs(local_path.parent, exist_ok=True)
        
        with open(local_path, 'wb') as f:
            content = file.decoded_content
            f.write(content)
        
        return str(local_path)
    
    def _get_files_recursive(self, repo: Repository, file_types: tuple, path: str, branch: str) -> List[ContentFile]:
        """Recursively get all files of specified types from repository."""
        files = []
        try:
            contents = repo.get_contents(path, ref=branch)
            
            if not isinstance(contents, list):
                contents = [contents]
            
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path, ref=branch))
                elif file_content.type == "file":
                    if not file_types or file_content.path.endswith(file_types):
                        files.append(file_content)
            
            return files
        except Exception as e:
            raise ValueError(f"Error accessing path '{path}' in repository: {str(e)}")
