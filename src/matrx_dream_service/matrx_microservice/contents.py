def get_gitignore_content():
    return """
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

temp/
"""


def get_conversions_content():
    return '''from matrx_connect.socket.schema import register_conversions

# Define your conversions methods here

def modify_mic_check(value):
    return str(value) + "[Converted by modify_mic_check]"


# Register Conversions

register_conversions({
    "convert_mic_check": modify_mic_check,

    # register more conversions here
})

# Example usage
# Replace "CONVERSION": None (inside schema.py), to "CONVERSION": "convert_mic_check"
'''


def get_validation_content():
    return '''from matrx_connect.socket.schema import register_validations

# Define your validation methods here

def validate_min_mic_check_message(value):
    if not len(value) > 50:
        raise ValueError("Value of of Mic check message must be greater than 50")

# Register Validations

register_validations({
    "validate_mic_check_min_length": validate_min_mic_check_message,

    # register more validations here
})

# Example usage
# Replace "VALIDATION": None (inside schema.py), to "VALIDATION": "validate_mic_check_min_length"
'''


def get_app_py_content():
    return '''import logging
from dotenv import load_dotenv
from socketio import ASGIApp

from matrx_utils import vcprint, settings
from matrx_connect import sio, get_user_session_namespace ,configure_factory
from matrx_connect.api import get_app
from services.app_factory import AppServiceFactory

load_dotenv()

import core.system_logger
import database_registry

logger = logging.getLogger("app")
logger.info("Starting application")

# Initialize / Register app schema
import app_schema
vcprint("Initialized app schema", color="bright_teal")


# Initialize service factory
configure_factory(AppServiceFactory)
vcprint("Service factory initialized", color="bright_teal")

# Create FastAPI app
app = get_app(settings.APP_NAME, settings.APP_DESCRIPTION, settings.APP_VERSION)
vcprint("FastAPI application created", color="green")

# Configure Socket.IO
socketio_app = ASGIApp(sio)
user_session_namespace = get_user_session_namespace()
sio.register_namespace(user_session_namespace)
app.mount("/socket.io", socketio_app)

vcprint("Socket.IO configured", color="green")

from mcp_server import register_all_mcp_tools
register_all_mcp_tools()


from matrx_orm import get_all_database_projects_redacted
from matrx_connect.socket import get_app_factory

def format_startup_output():
    print()
    vcprint("🚀 Application Startup Complete", color="bright_green")
    print()

    # Services section
    vcprint("📋 Registered Services:", color="cyan")
    services = get_app_factory().list_registered_service()
    if services:
        for service_name in services:
            vcprint(f"   ✓ {service_name}", color="light_green")
    else:
        vcprint("   (none)", color="gray")

    print()

    # Databases section
    vcprint("🗄️  Registered Databases:", color="light_blue")
    databases = get_all_database_projects_redacted()
    if databases:
        for i, db_conf in enumerate(databases, 1):
            vcprint(f"   Database {i}:", color="cyan")
            vcprint(f"     Host: {db_conf['host']}", color="white")
            vcprint(f"     Port: {db_conf['port']}", color="white")
            vcprint(f"     Database: {db_conf['database_name']}", color="white")
            vcprint(f"     User: {db_conf['user']}", color="white")
            vcprint(f"     Password: {db_conf['password']}", color="white")
            vcprint(f"     Alias: {db_conf['alias']}", color="white")
            vcprint(f"     Project: {db_conf['database_project']}", color="white")
            if i < len(databases):
                print()
    else:
        vcprint("   (none)", color="gray")
    print()
    vcprint(f"Base directory set to: {settings.BASE_DIR}", color="light_blue")
    print()


format_startup_output()
'''


def get_settings_content(app_name):
    return f'''from matrx_utils.conf import configure_settings
from pathlib import Path
from matrx_utils import vcprint
from dotenv import load_dotenv

load_dotenv()

class Settings:

    BASE_DIR = Path(__file__).resolve().parent.parent
    TEMP_DIR = BASE_DIR / "temp"
    ADMIN_PYTHON_ROOT = BASE_DIR
    ADMIN_TS_ROOT = TEMP_DIR

    LOCAL_LOG_DIR = TEMP_DIR / "logs"
    REMOTE_LOG_DIR = "/var/log/{app_name}"
    LOG_FILENAME = "{app_name}.log"



configure_settings(Settings, env_first=True)
vcprint("Settings initialized", "[settings.py]", color="green")
'''


def get_system_logger_content():
    return '''
import logging
import os
import sys
import logging.config
from matrx_utils.conf import settings
from matrx_utils import vcprint

def get_log_directory():
    if settings.ENVIRONMENT == "remote":
        path = settings.REMOTE_LOG_DIR
        os.makedirs(path, exist_ok=True)
        return path

    elif settings.ENVIRONMENT == "local":
        path = settings.LOCAL_LOG_DIR
        os.makedirs(path, exist_ok=True)
        return path

    else:
        raise ValueError("Invalid ENVIRONMENT in settings")


log_file_dir = get_log_directory()
if log_file_dir is None:
    raise ValueError("Cannot find log directory in settings")

os.makedirs(log_file_dir, exist_ok=True)

LOG_FILENAME = settings.LOG_FILENAME

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)-8s [%(name)s] %(message)s",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO" if settings.DEBUG else "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{log_file_dir}/{LOG_FILENAME}",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "standard",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "matrx_utils.vcprint": {
            "handlers": ["file"],
            "level": "DEBUG" if settings.LOG_VCPRINT else "CRITICAL",
            "propagate": False,
        },
        "app": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },
}

try:
    log_dir = os.path.dirname(LOGGING['handlers']['file']['filename'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.config.dictConfig(LOGGING)

except Exception as e:
    print(f"CRITICAL ERROR: Failed to configure logging: {e}", file=sys.stderr)


vcprint("[system_logger.py] Started System Logger")
'''


def get_docker_file_content(app_name):
    return f'''FROM python:3.13-slim
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_NAME={app_name}
ENV PROJECT_DIR=/app
ENV LOG_DIR=/var/log/{app_name}
ENV VIRTUAL_ENV=/app/.venv

# Set working directory
WORKDIR /app

# Install system dependencies required for the project
RUN apt-get update && apt-get install -y \\
    build-essential \\
    portaudio19-dev \\
    libasound2-dev \\
    libpulse-dev \\
    libmagic1 \\
    libpq-dev \\
    git \\
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Copy project files
COPY . /app/

# Install dependencies using UV
RUN uv sync --frozen

# Create necessary directories
RUN mkdir -p /var/log/{app_name} /app/temp/app_outputs /app/reports


COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
'''


def get_entrypoint_sh_content():
    return '''#!/bin/bash
# Disable exit on error to allow the script to continue even if a command fails
set +e

# Activate UV virtual environment
source /app/.venv/bin/activate

# Load environment variables from .env if it exists
if [ -f /app/.env ]; then
    echo "Loading environment variables from /app/.env"
    set -o allexport
    source /app/.env
    set +o allexport
else
    echo "/app/.env not found, proceeding without loading environment variables."
fi

# Ensure python-dotenv is installed
uv pip install python-dotenv

# Start the application
echo "Starting application..."
python run.py
'''


def get_run_py_content():
    return '''import uvicorn
from matrx_utils import settings, vcprint
import core.settings

if __name__ == "__main__":
    vcprint(
        f"Starting {settings.APP_NAME} version={settings.APP_VERSION} environment={settings.ENVIRONMENT} debug={settings.DEBUG}",
        color="bright_yellow"
    )
    uvicorn.run(
        "core.app:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=False
    )
'''


def get_migrations_content(app_name):
    return f"""import core.settings
import argparse
import database_registry
from matrx_utils import clear_terminal, vcprint, settings
from matrx_orm.schema_builder import SchemaManager
from matrx_orm.schema_builder.helpers.git_checker import check_git_status
from matrx_orm import get_all_database_project_names

clear_terminal()

ADMIN_SAVE_DIRECT_ROOT = settings.ADMIN_SAVE_DIRECT_ROOT
ADMIN_PYTHON_ROOT = settings.ADMIN_PYTHON_ROOT
ADMIN_TS_ROOT = settings.ADMIN_TS_ROOT

# Set up command-line argument parsing
parser = argparse.ArgumentParser(description="Database schema migration utility")
parser.add_argument("--database-project", help="Name of the database project")
parser.add_argument("--create-all", help="Add this argument if you need to migrate all databases.")

args = parser.parse_args()

# Determine database_project value and whether to skip the prompt
if args.database_project:
    database_project = args.database_project
    auto_run = True
    run_all = False

elif args.create_all:
    database_project = args.database_project
    auto_run = True
    run_all = True

else:
    database_project = "{app_name}"
    auto_run = False

schema = "public"
additional_schemas = ["auth"]
save_direct = ADMIN_SAVE_DIRECT_ROOT

if save_direct:
    check_git_status(save_direct)
    vcprint(
        "\\n[MATRX AUTOMATED SCHEMA GENERATOR] WARNING!! save_direct is True. Proceed with caution.\\n",
        color="red",
    )
    if not auto_run:
        input("WARNING: This will overwrite the existing schema files. Press Enter to continue...")

if run_all:
    todo_migrations = get_all_database_project_names()
else:
    todo_migrations = [database_project]

vcprint(f'Running migrations for projects {{todo_migrations}}')

for project in todo_migrations:

    schema_manager = SchemaManager(
        schema=schema,
        database_project=project,
        additional_schemas=additional_schemas,
        save_direct=save_direct,
    )
    schema_manager.initialize()

    matrx_schema_entry = schema_manager.schema.generate_schema_files()
    matrx_models = schema_manager.schema.generate_models()

    analysis = schema_manager.analyze_schema()
    vcprint(
        data=analysis,
        title="Schema Analysis",
        pretty=True,
        verbose=False,
        color="yellow",
    )

    schema_manager.schema.code_handler.print_all_batched()

"""

def get_admin_service_content():
    return """from matrx_connect.socket.services import AdminServiceBase
from matrx_orm import get_all_database_projects_redacted
class AdminService(AdminServiceBase):

    def __init__(self):
        super().__init__()

    async def get_registered_databases(self):
        database_configs = get_all_database_projects_redacted()
        try:
            await self.stream_handler.send_data(database_configs)
        except Exception as e:
            await self.stream_handler.send_error(
                    user_visible_message="Sorry, unable to complete the {task_name.lower()} task. Please try again later.",
                    message="Task returned no content",
                    error_type="task_failed"
                    )
        finally:
            await self.stream_handler.send_end()


    # async def test_database_connection(self):
    #     pass"""

def generate_readme(app_name):
    return f"""
# {app_name.capitalize()} Microservice

## Installation and Migrations

```bash
uv sync
```

For running migrations for a specific database project, use the following command:

```bash
uv run --active migrations.py --database-project {app_name}
```

For running migrations for all database projects available, use:

```bash
uv run --active migrations.py --create-all true
```

## Structure and Usage

### App Orchestrator and Business logic
- `src/<app_name>/<app_name>_orchestrator.py` is the file which brings all the business logic together.
- Everything in `src/<app_name>/ can contain the actual logic for the service.


### App Orchestrator logic affects following connections:

Any change to business logic will IMMEDIATELY affect the following connections:
- MCP Connection
- Socket IO Connection
- API Connection

"""
