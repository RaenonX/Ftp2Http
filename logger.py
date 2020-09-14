import logging
from logging.config import dictConfig

__all__ = ("apply_log_config", "log_exception")

from typing import Optional


def apply_log_config():
    dictConfig({
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default"
            },
            "console_handler": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": "logs/console.log",
                "formatter": "default",
                "mode": "a"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["wsgi", "console_handler"]
        }
    })


def log_exception(message: Optional[str] = None):
    logging.exception(message)
