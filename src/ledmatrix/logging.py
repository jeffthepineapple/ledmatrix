"""Small logging convenience wrapper."""
from __future__ import annotations

import logging
from typing import Optional


LOGGER_NAME = "ledmatrix"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(LOGGER_NAME if name is None else "%s.%s" % (LOGGER_NAME, name))


def configure_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
