import os
from pathlib import Path
from github import Github, GithubException
from urllib.parse import urlparse
import base64

class GitHubService:
    def __init__(self, token=None):
        """Initialize GitHub service with optional token."""
        self.github = Github(token) if token else Github()

    def parse_github_url(self, url: str) -> tuple:
        """Parse GitHub URL to extract owner, repo, branch, and path.
        Example:
            Input: https://github.com/huggingface/transformers/tree/main/docs/source/en/tasks
            Output: ('huggingface', 'transformers', 'main', 'docs/source/en/tasks')
        """
        try:
            # Remove 'https://github.com/' if present
            if 'github.com' in url:
                url = url.split('github.com/')[-1]
            
            # Split the remaining path
            parts = url.strip('/').split('/')
            
            if len(parts) < 2:
                raise ValueError("Invalid GitHub URL format. Must contain owner and repository name.")
            
            owner = parts[0]
            repo = parts[1]
            
            # Handle tree/blob paths
            if len(parts) > 2:
                if parts[2] == 'tree' or parts[2] == 'blob':
                    branch = parts[3]
                    folder_path = '/'.join(parts[4:]) if len(parts) > 4 else ""
                else:
                    branch = "main"
                    folder_path = '/'.join(parts[2:])
            else:
                branch = "main"
                folder_path = ""
            
            return owner, repo, branch, folder_path
            
        except Exception as e:
            raise ValueError(f"Invalid GitHub URL format: {str(e)}")

    def get_repository_files(self, repo_url: str, branch: str, folder_path: str = "", file_types=None) -> list:
        """Get list of files from repository matching specified criteria."""
        try:
            # Parse the repository URL
            owner, repo_name = self.parse_github_url(repo_url)[:2]
            
            # Clean the repository path
            repo_path = f"{owner}/{repo_name}"
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            
            # Get the repository
            repo = self.github.get_repo(repo_path)
            
            if not file_types:
                file_types = ['.md', '.mdx', '.rst', '.rstx', '.py', '.html']
            
            files = []
            try:
                if folder_path:
                    contents = repo.get_contents(folder_path, ref=branch)
                else:
                    contents = repo.get_contents("", ref=branch)
                
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path, ref=branch))
                    else:
                        if any(file_content.path.endswith(ext) for ext in file_types):
                            files.append(file_content)
            
            except GithubException as e:
                raise Exception(f"Error accessing repository: {str(e)}")
            
            return files
        
        except Exception as e:
            raise Exception(f"Error fetching repository files: {str(e)}")

    def download_file(self, file_content, base_dir: str, owner: str, repo: str, branch: str, folder_path: str) -> str:
        """Download file from repository and save to local directory."""
        try:
            # Get the file's path relative to the folder_path
            file_path = file_content.path
            if folder_path and file_path.startswith(folder_path):
                relative_path = file_path[len(folder_path):].lstrip('/')
            else:
                relative_path = file_path
            
            # Create the folder name using only repo name and path
            folder_components = [repo]
            if folder_path:
                folder_components.extend(folder_path.strip('/').split('/'))
            folder_name = '_'.join(folder_components)
            
            # Create the full path for the file
            download_dir = Path(base_dir) / folder_name
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Create the full local path for the file
            local_path = download_dir / relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download and save the file
            content = base64.b64decode(file_content.content).decode('utf-8')
            local_path.write_text(content, encoding='utf-8')
            
            return str(local_path)
        
        except Exception as e:
            raise Exception(f"Error downloading file {file_content.path}: {str(e)}")

    def upload_file(self, local_path: str, repo_url: str, branch: str, target_path: str) -> bool:
        """Upload file to GitHub repository."""
        try:
            owner, repo_name = self.parse_github_url(repo_url)[:2]
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            file_info = {
                'path': local_path,
                'name': os.path.basename(local_path)
            }
            
            commit_message = f"Add translated file: {file_info['name']}"
            
            return self.upload_to_github(repo, file_info, target_path, branch, commit_message)
        
        except Exception as e:
            raise Exception(f"Error uploading file {local_path}: {str(e)}")

    def upload_to_github(self, repo, file_info: dict, target_path: str, branch: str, commit_message: str):
        """Upload a file to GitHub repository.
        Args:
            repo: GitHub repository object
            file_info: Dictionary containing file information ('path' and 'name')
            target_path: Target path in the repository
            branch: Repository branch
            commit_message: Commit message
        """
        try:
            # Read file content with UTF-8 encoding
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get just the filename from the full path
            file_name = os.path.basename(file_info['path'])
            
            # Create the target path in the repository
            if target_path:
                # If target_path is the last folder in the local path, use it directly
                local_folder = os.path.basename(os.path.dirname(file_info['path']))
                if local_folder == target_path:
                    repo_file_path = os.path.join(target_path, file_name)
                else:
                    # Otherwise, use the target_path as provided
                    repo_file_path = os.path.join(target_path, file_name)
            else:
                repo_file_path = file_name
            
            # Normalize path separators
            repo_file_path = repo_file_path.replace('\\', '/')
            
            try:
                # Check if file exists
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
        except Exception as e:
            raise Exception(f"Error uploading {file_info['name']}: {str(e)}")
