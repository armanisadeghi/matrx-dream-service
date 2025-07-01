from matrx_utils.conf import configure_settings
from pathlib import Path
from matrx_utils import vcprint


class Settings:

    BASE_DIR = Path(__file__).resolve().parent.parent
    TEMP_DIR = BASE_DIR / "temp"

    LOCAL_LOG_DIR = TEMP_DIR / "logs"
    REMOTE_LOG_DIR = "/var/log/{{cookiecutter.app_name}}"
    LOG_FILENAME = "{{cookiecutter.app_name}}.log"



configure_settings(Settings, env_first=True)
vcprint("Settings initialized", "[settings.py]", color="bright_teal")