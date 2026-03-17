import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Configure logger with both stdout and file handlers.

    Args:
        name: Logger name (typically __name__)
        log_dir: Directory to store log files

    Returns:
        Configured logger instance
    """
    Path(log_dir).mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Format: timestamp [level] logger_name: message
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Stdout handler (INFO and above)
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # File handler (DEBUG and above, rotated daily)
    log_file = Path(log_dir) / f"jarvis_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7  # Keep 7 days
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Module-level logger
logger = setup_logger(__name__)
