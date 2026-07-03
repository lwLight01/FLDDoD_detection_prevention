"""
shared/logger.py
----------------
Centralised structured logging configuration using Loguru.
Import this in every Python microservice entry point (main.py).

Usage:
    from shared.logger import get_logger
    log = get_logger(__name__)
    log.info("Service started")
    log.bind(client_id="abc123").warning("Low trust score detected")

Ref: docs/Architecture.md § Logging
"""

import sys
from loguru import logger


def configure_logging(log_level: str = "INFO", service_name: str = "ddos-system") -> None:
    """
    Configure Loguru with structured JSON output for production.
    Call once in main.py before any other logging.

    Args:
        log_level:    Logging level string (DEBUG, INFO, WARNING, ERROR).
        service_name: Name tag injected into every log record for log aggregation.
    """
    logger.remove()  # Remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        f"<cyan>{service_name}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console output (human-readable during development)
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        enqueue=True,  # Thread-safe async logging
    )

    # File output (JSON structured for ELK/Loki in production)
    logger.add(
        "logs/{service_name}.log".format(service_name=service_name),
        format="{time} {level} {name} {message}",
        level=log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz",
        serialize=True,   # JSON format
        enqueue=True,
    )


def get_logger(name: str):
    """
    Returns a Loguru logger bound with the calling module name.
    This is a convenience wrapper — Loguru's global logger is already
    configured by configure_logging(), so the returned object is the
    same singleton with a context bind for the module name.
    """
    return logger.bind(module=name)
