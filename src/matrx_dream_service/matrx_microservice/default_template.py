default_config = {
    "databases": [],
    "env": {
        "DEBUG": False,
        "ENVIRONMENT": "remote",
        "LOG_LEVEL": "INFO",
        "PORT": 8000,
        "LOG_VCPRINT": False
    },
    "settings": {
        "app_name": "matrx-service",
        "app_version": "0.0.1",
        "app_description": "Matrx basic microservice",
        "app_primary_service_name": "matrx",
        "app_primary_database_project": None,
        "requires_python": ">=3.12"
    },
    "dependencies": [
        "matrx-connect @ git+https://github.com/armanisadeghi/matrx-connect.git@main",
        "matrx-utils @ git+https://github.com/armanisadeghi/matrx-utils.git@main",
        "matrx-orm @ git+https://github.com/armanisadeghi/matrx-orm.git@main",
        "uvicorn",
        "pydantic-settings",
        "python-socketio",
        "requests"
    ],
    "schema": {},
    "files": [
        "__init__.py",
        "src/__init__.py",
        "requirements.txt",
        "pyproject.toml",
        "docker-compose.yml",
        "Dockerfile",
        ".env.example",
        ".gitignore",
        "README.md"
    ],
    "post_create_scripts": [
        "uv sync"
    ]
}
