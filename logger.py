import logging

__all__ = ("apply_log_config", "log_exception")

from typing import Optional


def apply_log_config():
    logging.basicConfig(
        filename="logs/console.log",
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )


def log_exception(message: Optional[str] = None):
    logging.exception(message)
