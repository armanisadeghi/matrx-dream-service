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


def create_repo_in_org(repo_name: str, description: str, private: bool = True,
                       auto_init: bool = False) -> dict:  # Changed to return dict with url and id
    try:
        resp = github_client.rest.repos.create_in_org(
            org=github_org,
            name=repo_name,
            description=description,
            private=private,
            auto_init=auto_init
        )
        repo_url = resp.parsed_data.html_url
        repo_id = resp.parsed_data.id
        vcprint(f"Repository created: {repo_url}", color="green")
        return {'repo_url': repo_url, 'repo_id': repo_id}
    except RequestFailed as e:
        raise ValueError(f"Failed to create repo: {e.response.status_code} - {e.response.text}")


def push_code_to_repo(repo_name: str, code_path: str,
                      access: list = None) -> dict:  # Changed param from username to access (list of dicts)
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
        main_sha = github_client.rest.git.get_ref(owner=github_org, repo=repo_name,
                                                  ref="heads/main").parsed_data.object_.sha
        github_client.rest.git.create_ref(owner=github_org, repo=repo_name, ref='refs/heads/dev', sha=main_sha)
        vcprint("[matrx-dream-service] Dev branch created.", color="green")

        if access:
            for entry in access:
                username = entry.get('username')
                if not username:
                    continue

                try:
                    perm_dict = entry.get('permission', {})
                    # Map permission dict to GitHub string role (highest to lowest)
                    if perm_dict.get('admin', False):
                        perm_str = 'admin'
                    elif perm_dict.get('maintain', False):
                        perm_str = 'maintain'
                    elif perm_dict.get('triage', False):
                        perm_str = 'triage'
                    elif perm_dict.get('push', False):
                        perm_str = 'push'
                    else:
                        perm_str = 'pull'  # Default to read-only
                    github_client.rest.repos.add_collaborator(owner=github_org, repo=repo_name, username=username,
                                                              permission=perm_str)
                    vcprint(f"[matrx-dream-service] User {username} added as collaborator with {perm_str} permission.",
                            color="green")
                except Exception as e:
                    vcprint(f"[matrx-dream-service] Error adding User {username} added as collaborator.",
                            color="red")

        repo_url = f"https://github.com/{github_org}/{repo_name}"
        # Fetch repo_id after creation
        resp = github_client.rest.repos.get(owner=github_org, repo=repo_name)
        repo_id = resp.parsed_data.id
        return {
            'repo_name': repo_name,
            'repo_url': repo_url,
            'repo_id': repo_id,
            'dev_branch': 'dev',
            'main_branch': 'main'
        }

    except (subprocess.CalledProcessError, RequestFailed, ValueError) as e:
        # Delete the repo on failure to avoid garbage
        try:
            github_client.rest.repos.delete(owner=github_org, repo=repo_name)
            vcprint(f"[matrx-dream-service] Repository {repo_name} deleted due to failure.", color="red")
        except RequestFailed as del_err:
            vcprint(
                f"[matrx-dream-service] Failed to delete repository {repo_name}: {del_err.response.status_code} - {del_err.response.text}",
                color="red")
        raise ValueError(f"Operation failed: {str(e)}")


def orchestrate_repo_creation(base_name: str, description: str, code_path: str, private: bool = True,
                              access: list = None) -> dict:  # Changed param from username to access
    try:
        repo_name = get_available_repo_name_in_org(base_name)
        create_info = create_repo_in_org(repo_name, description, private=private)
        push_info = push_code_to_repo(repo_name, code_path, access=access)
        return {
            'repo_name': repo_name,
            'repo_url': create_info['repo_url'],
            'repo_id': create_info['repo_id'],
            'dev_branch': 'dev',
            'main_branch': 'main'
        }
    except Exception as e:
        vcprint(f"[matrx-dream-service] Repo creation orchestration failed: {str(e)}", color="red")
        raise


def list_collaborators(repo_name: str) -> list:
    try:
        collaborators = github_client.rest.repos.list_collaborators(owner=github_org, repo=repo_name, affiliation='direct').parsed_data
        result = []
        for collab in collaborators:
            result.append({
                'username': collab.login,
                'permission': collab.permissions.model_dump()
                # This is a dict like {'admin': bool, 'push': bool, etc.}, but for simplicity, return the full permissions dict
            })
        return result
    except RequestFailed as e:
        raise ValueError(f"Failed to list collaborators: {e.response.status_code} - {e.response.text}")


def add_collaborator_with_permission(repo_name: str, username: str, permission: str = 'pull') -> None:
    valid_permissions = ['pull', 'push', 'triage', 'maintain', 'admin']
    if permission not in valid_permissions:
        raise ValueError(f"Invalid permission: {permission}. Must be one of {valid_permissions}.")

    github_client.rest.repos.add_collaborator(
        owner=github_org,
        repo=repo_name,
        username=username,
        permission=permission
    )
    vcprint(f"[matrx-dream-service] User {username} added as collaborator with {permission} permission.", color="green")


def add_collaborators(repo_name: str, access: list[dict]) -> dict:
    success = []
    failed = []
    permission_order = ['admin', 'maintain', 'triage', 'push', 'pull']  # Predefined order: highest to lowest
    for entry in access:
        username = entry.get('username')
        if not username:
            failed.append(username)
            continue
        perm_dict = entry.get('permission', {})
        selected_perm = None
        for perm in permission_order:
            if perm_dict.get(perm, False):
                selected_perm = perm
                break
        if not selected_perm:
            continue
        try:
            add_collaborator_with_permission(repo_name, username, selected_perm)
            success.append(username)
        except (RequestFailed, ValueError) as e:
            failed.append(username)
    return {'success': success, 'failed': failed}


def remove_collaborator(repo_name: str, username: str) -> None:
    github_client.rest.repos.remove_collaborator(
        owner=github_org,
        repo=repo_name,
        username=username
    )
    vcprint(f"[matrx-dream-service] User {username} removed as collaborator.", color="green")


def remove_collaborators(repo_name: str, usernames: list[str]) -> dict:
    success = []
    failed = []
    for username in usernames:
        try:
            remove_collaborator(repo_name, username)
            success.append(username)
        except RequestFailed as e:
            failed.append(username)
    return {'success': success, 'failed': failed}

