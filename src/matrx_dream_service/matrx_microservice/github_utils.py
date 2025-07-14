from matrx_utils import settings, vcprint
from githubkit import GitHub
from githubkit.exception import RequestFailed
import re
import random
import string
import os
import subprocess

github_client = None

if not github_client:
    github_client = GitHub(settings.GITHUB_PAT)
    vcprint("Github client initialized", color="green")

github_org = settings.GITHUB_ORG_NAME

def repo_exists_in_org(repo_name: str) -> bool:
    try:
        github_client.rest.repos.get(owner=github_org, repo=repo_name)
        return True
    except RequestFailed as e:
        if e.response.status_code == 404:
            return False
        raise

def get_repo_name(base_name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9 _-]', '', base_name)
    cleaned = re.sub(r'\s+', '_', cleaned)
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = cleaned.lower()
    cleaned = cleaned.strip('_')
    return cleaned

def get_available_repo_name_in_org(base_name: str) -> str:
    original = get_repo_name(base_name)
    if not original:
        raise ValueError("Please choose a sane project name.")
    
    attempts = 0
    while attempts < 50:  # Increased safety limit to ensure we find a unique one
        suffix_len = random.randint(3, 5)  # 3-5 chars, mix letters and digits
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=suffix_len))
        candidate = f"{original}_{suffix}"
        if not repo_exists_in_org(candidate):
            return candidate
        attempts += 1
    raise ValueError("Could not find a repo name")

def create_repo_in_org(repo_name: str, description: str, private: bool=True, auto_init: bool=False) -> str:
    try:
        resp = github_client.rest.repos.create_in_org(
            org=github_org,
            name=repo_name,
            description=description,
            private=private,
            auto_init=auto_init
        )
        repo_url = resp.parsed_data.html_url
        vcprint(f"Repository created: {repo_url}", color="green")
        return repo_url
    except RequestFailed as e:
        raise ValueError(f"Failed to create repo: {e.response.status_code} - {e.response.text}")

def push_code_to_repo(repo_name: str, code_path: str, username: str=None) -> dict:
    try:
        git_dir = os.path.join(code_path, '.git')
        if os.path.exists(git_dir):
            raise ValueError(f"Directory '{code_path}' already has a .git folder. Clean it or use a new directory.")
        
        # Normalize path for safe.directory (use forward slashes)
        safe_path = os.path.normpath(code_path).replace('\\', '/')
        
        # Mark the directory as safe before any git operations
        subprocess.check_call(['git', 'config', '--global', '--add', 'safe.directory', safe_path])
        
        # Initialize repo with main branch
        subprocess.check_call(['git', 'init', '--initial-branch=main', code_path])
        vcprint("[matrx-dream-service] Local repo initialized.", color="green")
    
        bot_name = settings.GITHUB_BOT_ACCOUNT_USERNAME
        bot_email = settings.GITHUB_BOT_EMAIL
        subprocess.check_call(['git', '-C', code_path, 'config', 'user.name', bot_name])
        subprocess.check_call(['git', '-C', code_path, 'config', 'user.email', bot_email])
        
        # Add all files
        subprocess.check_call(['git', '-C', code_path, 'add', '.'])
        
        # Check if there are files to commit
        status = subprocess.check_output(['git', '-C', code_path, 'status', '--porcelain']).decode('utf-8').strip()
        if not status:
            raise ValueError("No files found in the directory to commit.")
        
        # Commit
        subprocess.check_call(['git', '-C', code_path, 'commit', '-m', 'Initial commit'])
        
        # Add remote and push
        remote_url = f"https://oauth2:{settings.GITHUB_PAT}@github.com/{github_org}/{repo_name}.git"
        subprocess.check_call(['git', '-C', code_path, 'remote', 'add', 'origin', remote_url])
        subprocess.check_call(['git', '-C', code_path, 'push', 'origin', 'main'])
        vcprint("[matrx-dream-service] Code pushed to GitHub repo's main branch.", color="green")

        # Create dev branch using API
        main_sha = github_client.rest.git.get_ref(owner=github_org, repo=repo_name, ref="heads/main").parsed_data.object_.sha
        github_client.rest.git.create_ref(owner=github_org, repo=repo_name, ref='refs/heads/dev', sha=main_sha)
        vcprint("[matrx-dream-service] Dev branch created.", color="green")

        if username:
            github_client.rest.repos.add_collaborator(owner=github_org, repo=repo_name, username=username, permission='pull')
            vcprint(f"[matrx-dream-service] User {username} added as collaborator.", color="green")

        repo_url = f"https://github.com/{github_org}/{repo_name}"
        return {
            'repo_name': repo_name,
            'repo_url': repo_url,
            'dev_branch': 'dev',
            'main_branch': 'main'
        }

    except (subprocess.CalledProcessError, RequestFailed, ValueError) as e:
        # Delete the repo on failure to avoid garbage
        try:
            github_client.rest.repos.delete(owner=github_org, repo=repo_name)
            vcprint(f"[matrx-dream-service] Repository {repo_name} deleted due to failure.", color="red")
        except RequestFailed as del_err:
            vcprint(f"[matrx-dream-service] Failed to delete repository {repo_name}: {del_err.response.status_code} - {del_err.response.text}", color="red")
        raise ValueError(f"Operation failed: {str(e)}")

def orchestrate_repo_creation(base_name: str, description: str, code_path: str, private: bool=True, username: str=None) -> dict:
    try:
        repo_name = get_available_repo_name_in_org(base_name)
        create_repo_in_org(repo_name, description, private=private)
        return push_code_to_repo(repo_name, code_path, username=username)
    except Exception as e:
        vcprint(f"[matrx-dream-service] Repo creation orchestration failed: {str(e)}", color="red")
        raise