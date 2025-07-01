# {{cookiecutter.app_dirname}}/run.py

import uvicorn
from matrx_utils import settings, vcprint

if __name__ == "__main__":
    vcprint(
        f"Starting {{cookiecutter.app_name}} v{{cookiecutter.app_version}} env={{cookiecutter.app_environment}} debug={{cookiecutter.app_debug}}",
        color="bright_yellow"
    )
    uvicorn.run(
        "core.app:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=False
    )