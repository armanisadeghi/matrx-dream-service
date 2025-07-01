# {{cookiecutter.app_dirname}}/core/system_logger.py

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