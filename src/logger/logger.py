"""Centralised logging setup with daily rotation."""

import logging
import logging.handlers
import os
from pathlib import Path


_logger = logging.getLogger(__name__)


def get_logger(name: str, log_dir: str = "log", log_level: str = "INFO", log_file_prefix: str = "app") -> logging.Logger:
    """Return a logger that writes to console and a daily-rotating file.

    Args:
        name: Logger name (typically ``__name__`` of the calling module).
        log_dir: Directory where log files are written.
        log_level: One of DEBUG / INFO / WARNING / ERROR / CRITICAL.
        log_file_prefix: Base name for the log file (date suffix added automatically).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    _logger.debug("get_logger: start name=%s log_level=%s log_dir=%s", name, log_level, log_dir)
    logger = logging.getLogger(name)

    if logger.handlers:
        _logger.debug("get_logger: complete name=%s (reused existing logger)", name)
        return logger

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (new file each day, keep 30 days)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, f"{log_file_prefix}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    logger.addHandler(file_handler)

    _logger.debug("get_logger: complete name=%s", name)
    return logger
