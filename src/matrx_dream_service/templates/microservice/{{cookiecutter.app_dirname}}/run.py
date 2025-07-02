# {{cookiecutter.app_dirname}}/run.py

import uvicorn
from matrx_utils import settings, vcprint
import core.settings

if __name__ == "__main__":
    vcprint(
        f"Starting {settings.APP_NAME} version={settings.APP_VERSION} environment={settings.ENVIRONMENT} debug={settings.DEBUG}",
        color="bright_yellow"
    )
    uvicorn.run(
        "core.app:app",
        host="127.0.0.1",
        port=int(settings.PORT),
        reload=False
    )