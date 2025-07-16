# AI Matrx Service

## 1. Matrx Microservice Generator

### Overview

The `MicroserviceGenerator` class is a tool for generating microservice projects based on a configuration file or dictionary. 

Key features:
- Config-driven generation (merge user config with defaults).
- Supports local file output or direct push to a GitHub repo in an organization.
- Validates config for restricted task_names, service_names, field_names for socket schema

### Setup

1. Install dependencies via `uv venv`
2. Activate the generated environment
3. Sync dependencies using `uv sync`
4. Import the class: `from matrx_dream_service.matrx_microservice import MicroserviceGenerator`.
5. Setup a environment with variables with actual values:

```.env
GITHUB_PAT=your-personal-access-token # Personal Access token of org owner or a memeber with priviliges to manage repositories.
GITHUB_ORG_NAME="org-name"
BASE_DIR=current-working-dir
GITHUB_BOT_ACCOUNT_USERNAME="username" # initial contributions to the repo will show up with this username
GITHUB_BOT_EMAIL="email@gmail.com"
```

### Parameters

- `config_path` (str, optional): Path to JSON config file.
- `output_dir` (str, optional): Directory for generated files.
- `create_github_repo` (bool, default=False): If True, creates and pushes to a GitHub repo.
- `github_project_name` (str, optional): Base name for GitHub repo (auto-appends suffix if needed).
- `github_access` (list[dict], optional): List of collaborator access objects, e.g., `[ {"username": "user1", "permission": {"admin": True}}, {"username": "user2", "permission": {"push": True}} ]`. Permissions map to GitHub roles (admin, maintain, triage, push, pull).
- `config` (dict, optional): Direct config dict (bypasses file load).
- `github_project_description` (str, optional): Description for GitHub repo.
- `debug` (bool, default=False): Enable verbose logging.

### Return Value

`generate_microservice()` returns a dict with GitHub details if `create_github_repo=True` (e.g., `{'repo_name': '...', 'repo_url': '...', 'repo_id': ..., 'dev_branch': 'dev', 'main_branch': 'main'}`), else None.

### Usage Examples

#### 1. Basic Local Generation (From Config File)
Generate microservice files locally without GitHub.

```python
from dotenv import load_dotenv
load_dotenv()

from matrx_dream_service.matrx_microservice import MicroserviceGenerator

generator = MicroserviceGenerator(
    config_path="path/to/config.json",
    output_dir="path/to/output",
    debug=True
)
generator.generate_microservice()
```

#### 2. Local Generation with Direct Config Dict
Use a config dict instead of a file.

```python
from dotenv import load_dotenv
load_dotenv()

from matrx_dream_service.matrx_microservice import MicroserviceGenerator

sample_config = {
    "settings": {"app_name": "MyApp"},
    # ... other config keys ...
}

generator = MicroserviceGenerator(
    config=sample_config,
    output_dir="path/to/output",
    debug=False
)
generator.generate_microservice()
```

#### 3. Generation with GitHub Repo Creation (No Collaborators)
Create and push to a GitHub repo.

```python
from dotenv import load_dotenv
load_dotenv()

from matrx_dream_service.matrx_microservice import MicroserviceGenerator

resp = MicroserviceGenerator(
    config_path="path/to/config.json",
    output_dir="path/to/output",
    create_github_repo=True,
    github_project_name="my-project",
    github_project_description="My microservice project"
).generate_microservice()

print(resp)  # {'repo_name': '...', 'repo_url': '...', ...}
```

#### 4. Generation with GitHub and Collaborator Access
Add collaborators with specific permissions during repo creation.

```python
from dotenv import load_dotenv
load_dotenv()

from matrx_dream_service.matrx_microservice import MicroserviceGenerator

sample_access = [
    {"username": "jatin-dot-py", "permission": {"admin": True}},
    {"username": "matrx-bot", "permission": {"push": True}}
]

resp = MicroserviceGenerator(
    config_path="path/to/config.json",
    output_dir="path/to/output",
    create_github_repo=True,
    github_project_name="my-scraper",
    github_access=sample_access,
    github_project_description="Scraper microservice"
).generate_microservice()

print(resp)  # Includes repo details
```

#### 5. Debug Mode with All Options
Full usage with debug enabled.

```python
from dotenv import load_dotenv
load_dotenv()

from matrx_dream_service.matrx_microservice import MicroserviceGenerator

sample_access = [
    {"username": "testuser", "permission": {"maintain": True}},
    {"username": "botuser", "permission": {"triage": True, "push": True}}
]

sample_config = {
    # ... config dict ...
}

resp = MicroserviceGenerator(
    config=sample_config,
    output_dir="path/to/output",
    create_github_repo=True,
    github_project_name="advanced-project",
    github_access=sample_access,
    github_project_description="Advanced example",
    debug=True
).generate_microservice()

print(resp)
```



#### 6. CLI Usage
Create a new microservice project from a config file.

**Usage:**
```
matrx create-microservice --config <path> --output_dir <dir> [options]
```

**Required Arguments:**
- `--config`: Path to the JSON config file (e.g., `--config path/to/config.json`).
- `--output_dir`: Output directory for generated files (e.g., `--output_dir path/to/output`).

**Optional Arguments:**
- `--create_github_repo`: Flag to create and push to a GitHub repo (e.g., `--create_github_repo`).
- `--github_project_name`: Base name for the GitHub repo (required if `--create_github_repo` is set; e.g., `--github_project_name my-project`).
- `--github_project_description`: Description for the GitHub repo (e.g., `--github_project_description "My microservice"`).
- `--github_access_file`: Path to JSON file for collaborator access (e.g., `--github_access_file path/to/access.json`). Format: `[{"username": "user1", "permission": {"admin": true}}, ...]`.
- `--debug`: Enable debug mode for this command.

**Examples:**

1. Basic local generation:
   ```
   matrx create-microservice --config path/to/config.json --output_dir path/to/output
   ```

2. With GitHub repo creation:
   ```
   matrx create-microservice --config path/to/config.json --output_dir path/to/output --create_github_repo --github_project_name my-project --github_project_description "Example project"
   ```

3. With collaborators from JSON file and debug:
   ```
   matrx create-microservice --config path/to/config.json --output_dir path/to/output --create_github_repo --github_project_name my-project --github_access_file path/to/access.json --debug
   ```


## 2. 